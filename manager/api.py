# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=W0621
#
import functools
import time
import email.utils
from flask import (
    Blueprint, request, abort, session, jsonify
)
from manager.log import get_log
from manager.apikey import ApiKey
from manager.burst import Burst
from manager.component import Component
from manager.event import report, ReportReceived
from manager.exceptions import InvalidApiCall
from manager.reporter import registry

# establish blueprint
bp = Blueprint('api', __name__, url_prefix='/api')

# ---------------------------------------------------------------------------
#                                                                 CONSTANTS
# ---------------------------------------------------------------------------

# API version.  Simple integer; increment as needed.  Should match what is
# reported by the Detector.
API_VERSION = 2

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
  """
  Use this API to get list of burst candidates accepted for promotion to the
  burst pool.
  """

  get_log().debug("In api.api_get_bursts")

  cluster = Component(session['api_component']).cluster

  bursts = Burst.view(criteria={'cluster': cluster, 'view': 'adjustor'})
  return jsonify(bursts), 200

@bp.route('/bursts', methods=['POST'])
@api_key_required
def api_post_bursts():
  """
  Use this API to report on burst candidates and other actionable metrics
  related to users' use of resources.

  All reports must conform to the base API.  In the trivial case, this
  consists of the following:

  ```
  report = {
    version = 2
  }
  ```

  In most cases additional report sections will contain information gathered by
  Detectors.  Each section will be named for the type of report and will
  consist of a list of accounts, users and/or jobs, a trouble metric, and
  contextual information.  For example:

  ```
  report = {
    version = 2,
    bursts = [ ... ],
    job_age = [ ... ]
  }
  ```

  In this example the Detector is reporting on potential burst candidates as
  well as jobs where their age is of potential concern.  Each of these would
  be handled by a subclass of the Reporter base class.

  The Detector does not need to report the cluster where the detection occurs,
  since this information is associated with the API key the Detector uses.
  The Manager still needs to save this with the record.
  """

  get_log().debug("In api.post_bursts()")

  epoch = session['api_epoch']
  cluster = Component(session['api_component']).cluster
  get_log().debug("Receiving report for cluster %s", cluster)

  # check basic request validity.  At this stage only verify there is data,
  # that the version is specified and it matches the expected version.
  data = request.get_json()
  if (not data
      or data.get('version', None) is None
  ):
    errmsg = "API violation: must define 'version'"
    get_log().error(errmsg)
    abort(400, errmsg)
  if int(data['version']) != API_VERSION:
    errmsg = "Client API version ({}) does not match server ({})".format(
      int(data['version']), API_VERSION)
    get_log().error(errmsg)
    abort(400, errmsg)

  # run through reports.  For each, invoke appropriate class
  # TODO: two ways to make this easier to read:
  # 1. Just delete 'version' from data.  Possibly not as efficient as next,
  #    but easy to read
  # 2. Create generator like so:
  #    >>> def not_three(d):
  #    ...   for x in d.keys():
  #    ...     if x != 3:
  #    ...       yield((x, d[x]))
  #    Then:
  #    for (n, s) in not_three(d): etc.
  for (report_name, report_data) in { x: data[x] for x in data.keys() if x != 'version' }.items():

    # TODO: subclasses of Reporter should register their report names, so we
    #       can just loop through the registry here.
    try:
      reporter = registry.reporters[report_name]
    except KeyError as e:
      errmsg = "Unrecognized report type: {}".format(report_name)
      get_log().error(errmsg)
      abort(400, errmsg)

    try:
      summary = reporter.report(cluster, epoch, report_data)
    except InvalidApiCall as e:
      errmsg = "Does not conform to API for report type {}: {}".format(report_name, e)
      get_log().error(errmsg)
      abort(400, errmsg)

    # report that, um, report was received
    report(ReportReceived("{} on {}: {}".format(report_name, cluster, summary)))

  return jsonify({'status': 'OK'}), 201
