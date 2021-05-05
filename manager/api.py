# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=W0621
#
import re
import functools
import time
import email.utils
from flask import (
    Blueprint, request, abort, session, jsonify
)
from manager.log import get_log
from manager.apikey import ApiKey
from manager.burst import Burst, get_bursts, State, Resource
from manager.component import Component
from manager.event import report, BurstReportReceived

# establish blueprint
bp = Blueprint('api', __name__, url_prefix='/api')

# regular expression to match job array IDs and allow extraction of just ID
job_id_re = re.compile(r'^(\d+)')

# ---------------------------------------------------------------------------
#                                                                 CONSTANTS
# ---------------------------------------------------------------------------

# API version.  Simple integer; increment as needed.  Should match what is
# reported by the Detector.
API_VERSION = 1

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
      errmsg = "Missing authorization header"
      get_log().info(errmsg)
      abort(401, errmsg)
    get_log().debug("Authorization = %s", request.headers['Authorization'])

    # parse authorization header
    try:
      (marker, accesskey, digest) = request.headers['Authorization'].split()

      # check marker
      if marker != "BEAM":
        raise RuntimeError()
    except (RuntimeError, ValueError):
      # catches raised exception and also <3 strings to split above
      errmsg = "Invalid authorization header"
      get_log().error(errmsg)
      abort(401, errmsg)

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

      # aborting without explanatory text in case of malicious intent
      abort(401)

    # verify digest given against our own calculated from request
    try:
      if not apikey.verify(digestible, digest):
        get_log().error("Digests do not match")
        abort(401)
    except ValueError as e:
      get_log().error("Message authorization digest failure: '%s'", e)

      # aborting without explanatory text in case of malicious intent
      abort(401)

    # Check date is relatively recent.  Do this AFTER message digest
    # verification because it's to guard against replay attacks
    now = int(time.time())
    then = email.utils.mktime_tz(email.utils.parsedate_tz(datestamp))
    delta = now - then
    if delta > 300:
      get_log().warning("Out-of-date API request")

      # aborting without explanatory text in case of malicious intent
      abort(400)

    # update last-used timestamp
    apikey.update_use(now)

    # check for API version
    api_version = request.headers.get('apiversion', '0')

    session['api'] = True
    session['api_keyname'] = accesskey
    session['api_component'] = apikey.component
    session['api_version'] = api_version
    session['api_epoch'] = now

    get_log().debug("API key %s successfully authenticated", accesskey)

    return view(**kwargs)

  return wrapped_view

def summarize_burst_report(cluster, bursts):

  # counts
  newbs = 0
  existing = 0
  claimed = 0
  by_state = {
    State.PENDING: 0,
    State.ACCEPTED: 0,
    State.REJECTED: 0
  }

  for burst in bursts:
    if burst.ticks > 0:
      existing += 1
    else:
      newbs += 1

    if burst.claimant:
      claimed += 1

    by_state[State(burst.state)] += 1

  return "A new burst report came in from {} with {} new burst record(s)" \
    " and {} existing.  In total there are {} pending, {} accepted," \
    " {} rejected.  {} have been claimed.".format(
      cluster, newbs, existing, by_state[State.PENDING],
      by_state[State.ACCEPTED], by_state[State.REJECTED], claimed
    )

# ---------------------------------------------------------------------------
#                                                                 BURST API
# ---------------------------------------------------------------------------

@bp.route('/bursts/<int:id>', methods=['GET'])
@api_key_required
def api_get_burst(id):

  get_log().debug("In api.get_burst(%d)", id)
  return jsonify(Burst(id=id))

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
      version = 1,
      bursts = [
        {
          'account':  character string representing CC account name,
          'resource': type of resource involved in burst (ex. 'cpu', 'gpu'),
          'pain':     number indicating pain ratio as defined by Detector,
          'firstjob': first job owned by account currently in the system,
          'lastjob':  last job owned by account currently in the system,
          'submitters': array of user IDs of those submitting jobs,
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

  epoch = session['api_epoch']
  cluster = Component(session['api_component']).cluster
  get_log().debug("Registering burst for cluster %s", cluster)

  # check basic request validity
  data = request.get_json()
  if (not data
      or data.get('version', None) is None
      or data.get('bursts', None) is None
  ):
    errmsg = "API violation: must define both 'version' and 'bursts'"
    get_log().error(errmsg)
    abort(400, errmsg)
  if int(data['version']) != API_VERSION:
    errmsg = "Client API version ({}) does not match server ({})".format(
      int(data['version']), API_VERSION)
    get_log().error(errmsg)
    abort(400, errmsg)

  # build list of burst objects from report
  bursts = []
  for burst in data['bursts']:

    # get the submitted data
    try:
      # pull the others
      res_raw = burst['resource']
      account = burst['account']
      pain = burst['pain']
      summary = burst['summary']
      submitters = burst['submitters']

      # strip job array ID component, if present
      firstjob = just_job_id(burst['firstjob'])
      lastjob = just_job_id(burst['lastjob'])

    except KeyError as e:
      # client not following API
      errmsg = "Missing field required by API: {}".format(e)
      get_log().error(errmsg)
      abort(400, errmsg)

    # convert from JSON representations
    try:
      resource = Resource.get(res_raw)
    except KeyError as e:
      errmsg = "Invalid resource type: {}".format(e)
      get_log().error(errmsg)
      abort(400, errmsg)

    # create burst and append to list
    bursts.append(Burst(
      cluster=cluster,
      account=account,
      resource=resource,
      pain=pain,
      submitters=submitters,
      jobrange=(firstjob, lastjob),
      summary=summary,
      epoch=epoch
    ))

  # report event
  summary = summarize_burst_report(cluster, bursts)
  report(BurstReportReceived(summary))

  return jsonify({'status': 'OK'}), 201
