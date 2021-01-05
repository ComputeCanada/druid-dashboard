# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
import functools

from flask import (
  Blueprint, g, request, session
)
from werkzeug.exceptions import abort

from app.log import get_log
from app.ldap import get_ldap

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
      abort(404)
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

      # this flags whether user is fully authenticated (i.e. user information
      # is loaded from LDAP)
      authenticated_externally = False

      # check if externally authenticated
      if authenticated_user:

        # get user information into session
        details = get_ldap().get_person(
          authenticated_user, ['eduPersonEntitlement'])
        get_log().debug("LDAP details for %s: %s", authenticated_user, details)

        if details:
          try:
            for key in ['cn', 'cci', 'givenName', 'preferredLanguage']:
              session[key] = details[key]
          except KeyError:
            # all of these are required and/or present in a valid user
            # representing a real user, so without them the app is forbidden
            abort(403)

          # set this after the rest as this establishes a valid authentication
          session['uid'] = authenticated_user

          # check if user has rights to this service
          if 'eduPersonEntitlement' in details:

            # has admin rights?
            session['admin'] = 'frak.computecanada.ca/burst/admin' in details['eduPersonEntitlement']

            # default for those with admin rights is to show admin view
            session['admin_view'] = session['admin']

            # has analyst rights?
            session['analyst'] = 'frak.computecanada.ca/burst/analyst' in details['eduPersonEntitlement']

          else:
            session['admin'] = False
            session['admin_view'] = False
            session['analyst'] = False

          load_logged_in_user()
          authenticated_externally = True

          session['authenticated_externally'] = True

      if not authenticated_externally:
        abort(403)

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
