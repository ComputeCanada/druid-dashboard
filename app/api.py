# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=W0621
#
import functools
from datetime import datetime, timezone
import email.utils
from flask import (
    Blueprint, request, abort, session, jsonify
)
from app.log import get_log
from app.apikey import ApiKey
from app.burst import Burst
from app.component import Component

# establish blueprint
bp = Blueprint('api', __name__, url_prefix='/api')

# ---------------------------------------------------------------------------
#                                                                    HELPERS
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
#                                                                     BURST
#                                                                     API
# Manager records burst report ID with each burst record.  Current bursts
# are only what were reported in last report.
#
# v0:
#   bursts:
#     rapi: char(10)
#     pain: float
#     firstjob: integer
#     lastjob: integer
#     summary:
#       jobs_total: integer (standby, queued, running)
#       cpus_total: integer
#       mem_total: integer
#
# Detector does not need to report the cluster where the burst occurs, since
# this information is associated with the API key the Detector uses.  The
# Manager still needs to save this with the record.
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

  # get query parameters
  #cluster = request.args.get('cluster', None)

  # TODO: bursts = get_bursts(cluster=cluster)
  bursts = ({})
  return bursts

@bp.route('/bursts', methods=['POST'])
@api_key_required
def api_post_bursts():

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
      bursts.append(Burst(
        cluster=cluster,
        account=burst['rapi'],
        pain=burst['pain'],
        jobrange=(burst['firstjob'], burst['lastjob']),
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
