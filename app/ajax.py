# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#

from flask import Blueprint, jsonify, request

from app.auth import admin_required
from app.log import get_log
from app.apikey import get_apikeys, add_apikey, delete_apikey


bp = Blueprint('ajax', __name__, url_prefix='/xhr')

# ---------------------------------------------------------------------------
#                                                          DATABASE HELPERS
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
#                                                                   HELPERS
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
#                                                   ROUTES - authorizations
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
#                                                         ROUTES - API keys
# ---------------------------------------------------------------------------

@bp.route('/apikeys/', methods=('GET',))
@admin_required
def xhr_get_apikeys():

  access_keys = get_apikeys()
  return jsonify(access_keys)


@bp.route('/apikeys/', methods=('POST',))
@admin_required
def xhr_add_apikey():

  access = request.form['apikey_name']
  secret = request.form['apikey']
  get_log().debug("Adding API key (%s)", access)
  try:
    add_apikey(access, secret)
  except Exception as e:
    get_log().error("Exception in adding API key (%s=%s): %s", access, secret, e)
    return None
  return jsonify({'status': 'OK'}), 200


@bp.route('/apikeys/<string:access>', methods=('DELETE',))
@admin_required
def xhr_delete_apikey(access):

  get_log().debug("Deleting API key: %s", access)
  try:
    delete_apikey(access)
  except Exception as e:
    get_log.error("Exception in deleting API key: %s", e)

    # I cannot figure out how to respond in such a way that indicates error, except
    # not to respond at all.  Have not tried using 4xx HTTP response status because
    # that is not necessarily appropriate
    #return jsonify({'status': 'error'}), 200
    return None

  return jsonify({'status': 'OK'}), 200

# ---------------------------------------------------------------------------
#                                               ROUTES - site configuration
# ---------------------------------------------------------------------------
