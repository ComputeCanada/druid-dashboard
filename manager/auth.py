# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=assigning-non-slot
# NOTE: "assigning-non-slot" test is broken in Pylint; can remove when
#       https://github.com/PyCQA/pylint/issues/3793 resolved
#
import functools

from flask import (
  Blueprint, g, request, session
)
from werkzeug.exceptions import abort

from manager.log import get_log
from manager.authz import NotAuthorized
from manager.authz_ccldap import CcLdapAuthz

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.before_app_request
def load_logged_in_user():
  user_id = session.get('uid')

  if user_id is None:
    g.user = None
  else:
    g.user = {
      'id': session['uid'],
      'cn': session['cn'],
      'cci': session['cci'],
      'admin': session['admin']
    }


def admin_required(view):
  @functools.wraps(view)
  def wrapped_view(**kwargs):
    if not session.get('admin'):
      abort(403)
    return view(**kwargs)
  return wrapped_view


def login_required(view):
  @functools.wraps(view)
  def wrapped_view(**kwargs):

    if g.user is None:

      # clear any existing login cruft
      session.clear()

      authenticated_user = None

      # use mapping in reverse proxy configuration to map REMOTE_USER from
      # authentication module to X_AUTHENTICATED_USER
      if 'X_AUTHENTICATED_USER' in request.headers:
        authenticated_user = request.headers['X_AUTHENTICATED_USER']
      get_log().debug("X_AUTHENTICATED_USER = %s", authenticated_user)

      # check if externally authenticated
      if not authenticated_user:
        get_log().error("User not authenticated")
        abort(403)

      # determine authorization
      ### TODO: use generic get_authz() set up in __init__
      try:
        authz = CcLdapAuthz(authenticated_user)
      except NotAuthorized as e:
        get_log().warning("Unauthorized user: %s", e)
        abort(403)

      # get user information into session
      session['uid'] = authenticated_user
      session['cn'] = authz.name
      session['givenName'] = authz.given
      session['cci'] = authz.id

      # set authorizations in session
      session['admin'] = False
      session['analyst'] = False
      if authz.entitlements:
        # This is necessary here because Pylint recognizes that entitlements
        # might be `None`, but does not recognize that this was tested for
        # already.  Not sure of a more Pythonic way of doing this.
        # pylint: disable=unsupported-membership-test
        session['admin'] = 'admin' in authz.entitlements
        session['analyst'] = 'analyst' in authz.entitlements
      session['admin_view'] = session['admin']

      if not session['analyst'] and not session['admin']:
        get_log().warning("Unauthorized user (missing entitlements): %s",
          authenticated_user)
        abort(403)

      load_logged_in_user()

    # TODO: not sure, this may be useful with SSE
    #notifications = get_db().execute(
    #  'SELECT result FROM notifications WHERE user_id = ? AND NOT seen',
    #  (g.user['id'],)
    #)
    #for notification in notifications:
    #  get_log().debug("Retrieved notification: '%s'", notification['result'])
    #  flash(Markup('Notification: %s' % notification['result']))
    #get_db().execute('UPDATE notifications SET seen = true WHERE user_id = ?', (g.user['id'],))
    #get_db().commit()

    return view(**kwargs)

  return wrapped_view
