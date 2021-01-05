# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=W0621
#
import functools
from datetime import datetime, timezone
import email.utils
from flask import (
    Blueprint, request, abort, session
)
from app.log import get_log
from app.apikey import verify_message

# establish blueprint
bp = Blueprint('api', __name__, url_prefix='/api')

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
      abort(403)
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
      abort(403)

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

    # verify digest given against our own calculated from request
    try:
      if not verify_message(accesskey, digestible, digest, update_used=True):
        get_log().error("Digests do not match")
        abort(403)
    except ValueError as e:
      get_log().error("Message authorization digest failure: '%s'", e)
      abort(403)

    # Check date is relatively recent.  Do this AFTER message digest
    # verification because it's to guard against replay attacks
    now = datetime.now(timezone.utc)
    then = email.utils.parsedate_to_datetime(datestamp)
    delta = now - then
    if delta.total_seconds() > 300:
      get_log().warning("Out-of-date API request")
      abort(400)

    session['api'] = True
    session['api_keyname'] = accesskey

    return view(**kwargs)

  return wrapped_view

# ---------------------------------------------------------------------------
#                                                                     ROUTES
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

  data = request.form
  # TODO: remove--this is only to avoid lint warnings
  print(data)

  # TODO: burst = Burst(data)

  # if burst:
  return ('OK', 201)
