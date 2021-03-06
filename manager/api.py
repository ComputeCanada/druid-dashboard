# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=W0621
#
import functools
import time
import email.utils
from flask import (
    Blueprint, request, abort, session, jsonify
)
from manager.errors import xhr_error
from manager.log import get_log
from manager.apikey import ApiKey
from manager.component import Component
from manager.event import report, ReportReceived
from manager.exceptions import InvalidApiCall
from manager.case import registry, Case

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
  get_log().error("Bad request (error = %s)", error)
  return jsonify({'error': str(error)}), 400

@bp.errorhandler(401)
def unauthorized(error):
  get_log().error("Unauthorized (error = %s)", error)
  return jsonify({'error': str(error)}), 401

@bp.errorhandler(403)
def forbidden(error):
  get_log().error("Forbidden (error = %s)", error)
  return jsonify({'error': str(error)}), 403

@bp.errorhandler(500)
def servererror(error):
  get_log().error("Server error (error = %s)", error)
  return jsonify({'error': str(error)}), 500

# ---------------------------------------------------------------------------
#                                                                    HELPERS
# ---------------------------------------------------------------------------

def items_except(d, unkeys):
  for k, v in d.items():
    if k not in unkeys:
      yield k, v

def api_key_required(view):
  @functools.wraps(view)
  def wrapped_view(**kwargs):

    # check for authorization header
    if 'Authorization' not in request.headers:
      errmsg = "Missing authorization header"
      get_log().info(errmsg)
      abort(401, errmsg)

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

    get_log().info("API key %s successfully authenticated", accesskey)

    return view(**kwargs)

  return wrapped_view

# ---------------------------------------------------------------------------
#                                                                 BURST API
# ---------------------------------------------------------------------------

@bp.route('/cases/<int:id>', methods=['GET'])
@api_key_required
def api_get_case(id):

  case = Case.get(id)
  if not case:
    return xhr_error(404, "No case found matching ID %d", id)
  return jsonify(case)

@bp.route('/cases/', methods=['GET'])
@api_key_required
def api_get_cases():
  """
  Use this API to get list of burst candidates accepted for promotion to the
  burst pool.
  """

  cluster = Component(session['api_component']).cluster
  criteria = {
    'cluster': cluster
  }

  reporter = None
  report_specified = False
  for k, v in request.args.items():
    if k == "report":
      report_specified = True
      reporter = registry.reporters[v]
    else:
      criteria[k] = v

  if not report_specified:
    return xhr_error(400, "Request did not specify report")
  if not reporter:
    return xhr_error(400, "Requested report not recognized")

  cases = reporter.view(criteria=criteria)
  return jsonify(cases), 200

@bp.route('/cases/', methods=['POST'])
@api_key_required
def api_post_cases():
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

  epoch = session['api_epoch']
  cluster = Component(session['api_component']).cluster

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

  # default status is 200 in case there isn't anything actually
  # created/updated
  status = 200

  # run through reports.  For each, invoke appropriate class
  for report_name, report_data in items_except(data, ('version',)):

    try:
      reporter = registry.reporters[report_name]
    except KeyError as e:
      return xhr_error(400, "Unrecognized report type: %s", report_name)

    try:
      summary = reporter.report(cluster, epoch, report_data)
    except InvalidApiCall as e:
      return xhr_error(400, "Does not conform to API for report type %s: %s", report_name, e)

    # report that, um, report was received
    report(ReportReceived("{} on {}: {}".format(report_name, cluster, summary)))

    status = 201

  return jsonify({'status': status}), status
