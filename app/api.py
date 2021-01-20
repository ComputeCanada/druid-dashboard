# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=W0621
#
import re
import functools
from datetime import datetime, timezone
import email.utils
from flask import (
    Blueprint, request, abort, session, jsonify
)
from app.log import get_log
from app.apikey import ApiKey
from app.burst import Burst, get_bursts
from app.component import Component

# establish blueprint
bp = Blueprint('api', __name__, url_prefix='/api')

# regular expression to match job array IDs and allow extraction of just ID
job_id_re = re.compile(r'^(\d+)(_\d+)?$')

# ---------------------------------------------------------------------------
#                                                            ERROR HANDLERS
# ---------------------------------------------------------------------------

@bp.errorhandler(400)
def badrequest(error):
  get_log().error("Forbidden (error = %s)", error)
  return jsonify({'error': str(error)}), 400

@bp.errorhandler(401)
def unauthorized(error):
  get_log().error("Forbidden (error = %s)", error)
  return jsonify({'error': str(error)}), 401

@bp.errorhandler(403)
def forbidden(error):
  get_log().error("Forbidden (error = %s)", error)
  return jsonify({'error': str(error)}), 403

@bp.errorhandler(500)
def servererror(error):
  get_log().error("Forbidden (error = %s)", error)
  return jsonify({'error': str(error)}), 500

# ---------------------------------------------------------------------------
#                                                                    HELPERS
# ---------------------------------------------------------------------------

def just_job_id(jobid):
  """
  Strip job ID to just the base ID, not including any array part.
  """
  if isinstance(jobid, int):
    return jobid
  match = job_id_re.match(jobid)
  if not match:
    raise Exception("Could not parse job ID ('{}') to extract base ID".format(jobid))
  return match.groups()[0]


def api_key_required(view):
  @functools.wraps(view)
  def wrapped_view(**kwargs):

    get_log().debug("In api_key_required()")

    # check for authorization header
    if 'Authorization' not in request.headers:
      get_log().info("Missing authorization header")
      abort(401)
    get_log().debug("Authorization = %s", request.headers['Authorization'])

    # parse authorization header
    try:
      (marker, accesskey, digest) = request.headers['Authorization'].split()

      # check marker
      if marker != "BEAM":
        raise RuntimeError()
    except (RuntimeError, ValueError):
      # catches raised exception and also <3 strings to split above
      get_log().error("Invalid authorization header")
      abort(401)

    # request.date NOT used because it reinterprets date according to locale
    datestamp = request.headers['date']

    # build resource string
    resource = request.path
    if request.args:
      resource += "?{}".format(
        '&'.join(['='.join(kv) for kv in sorted(request.args.items())])
      )

    # determine string to digest
    digestible = "{} {}\n{}".format(request.method, resource, datestamp)

    # get API key object
    try:
      apikey = ApiKey(accesskey)
    except ValueError as e:
      get_log().error("Could not find API key %s", accesskey)
      abort(401)

    # verify digest given against our own calculated from request
    try:
      if not apikey.verify(digestible, digest):
        get_log().error("Digests do not match")
        abort(401)
    except ValueError as e:
      get_log().error("Message authorization digest failure: '%s'", e)
      abort(401)

    # Check date is relatively recent.  Do this AFTER message digest
    # verification because it's to guard against replay attacks
    now = datetime.now(timezone.utc)
    then = email.utils.parsedate_to_datetime(datestamp)
    delta = now - then
    if delta.total_seconds() > 300:
      get_log().warning("Out-of-date API request")
      abort(400)

    # check for API version
    api_version = request.headers.get('apiversion', '0')

    session['api'] = True
    session['api_keyname'] = accesskey
    session['api_component'] = apikey.component
    session['api_version'] = api_version

    get_log().debug("API key %s successfully authenticated", accesskey)

    return view(**kwargs)

  return wrapped_view

# ---------------------------------------------------------------------------
#                                                                 BURST API
# ---------------------------------------------------------------------------

@bp.route('/bursts/<int:id>', methods=['GET'])
@api_key_required
def get_burst(id):

  get_log().debug("In api.get_burst(%d)", id)

  # TODO: burst = Burst(id)
  burst = {}
  return burst

@bp.route('/bursts', methods=['GET'])
@api_key_required
def api_get_bursts():

  get_log().debug("In api.api_get_bursts")

  cluster = Component(session['api_component']).cluster

  bursts = get_bursts(cluster=cluster)
  return jsonify(bursts), 200

@bp.route('/bursts', methods=['POST'])
@api_key_required
def api_post_bursts():
  """
  Post a Burst Report: a list of accounts and information about their current
  job context which constitutes a potential burst candidate.

  Format:
    ```
    report = {
      [
        {
          'account':  10-character string representing CC RAPI,
          'pain':     number indicating pain ratio as defined by Detector,
          'jobrange': tuple of (firstjob, lastjob) owned by account and
                      currently in the system
          'summary':  JSON-encoded key-value information about burst context
                      which may be of use to analyst in evaluation
        },
        ...
      ]
    }
    ```

  The `jobrange` is used by the Manager and Scheduler to provide a way by
  which the Scheduler can decide to "unbless" an account--no longer promote it
  or its jobs to the Burst Pool--without the Detector or the Scheduler needing
  to maintain independent state.

  When the Detector signals a potential burst, it reports the first and last
  jobs (lowest- and highest-numbered) in every report.  The Manager compares
  this to existing burst candidates.  If the new report overlaps with an
  existing one, the Manager updates its current understanding with the new upper
  range.  (The lower range is not updated as this probably only reflects that
  earlier jobs have been completed, although in the case of mass job deletion
  this would be misleading, but this range is not intended to be used for any
  analyst decisions.)

  The Detector may report several times a day and so will report the same
  burst candidates multiple times.

  The Scheduler retrieves affirmed Burst candidates from the Manager.  When
  a new candidate is pulled, the Scheduler promotes the account to the burst
  pool.  That account will be provided on every query by the Scheduler, with
  the job range updated as necessary based on information received by the
  Manager from the Detector.  Even once the Detector no longer reports this
  account as a burst candidate, the Manager will maintain its record.

  The Scheduler will compare the burst record against jobs currently in the
  system.  If no jobs exist owned by the account that fall within the burst
  range, then the burst must be complete.  The Scheduler must then report the
  burst as such to the Manager.

  The Detector does not need to report the cluster where the burst occurs,
  since this information is associated with the API key the Detector uses.
  The Manager still needs to save this with the record.
  """

  get_log().debug("In api.post_bursts()")

  cluster = Component(session['api_component']).cluster
  get_log().debug("Registering burst for cluster %s", cluster)
  bursts = []
  data = request.get_json()
  if not data or not data.get('report', None):
    get_log().error("API violation: must include 'report' definition")
    abort(400)
  try:
    for burst in data['report']:
      get_log().debug("Received burst information for account %s", burst['rapi'])

      # strip job array ID component, if present
      firstjob = just_job_id(burst['firstjob'])
      lastjob = just_job_id(burst['lastjob'])

      # create burst and append to list
      bursts.append(Burst(
        cluster=cluster,
        account=burst['rapi'],
        pain=burst['pain'],
        jobrange=(firstjob, lastjob),
        summary=burst['summary']
      ))
  except KeyError as e:
    # client not following API
    get_log().error("Missing field required by API: %s", e)
    abort(400)
  except Exception as e:
    get_log().error("Could not register burst: '{}'".format(e))
    abort(500)

  return jsonify({'status': 'OK'}), 201
