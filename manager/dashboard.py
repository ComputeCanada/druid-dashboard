# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
from time import sleep
from flask import (
  stream_with_context, Blueprint, render_template, url_for, session, redirect,
  request, Response
)

from manager.auth import login_required
from manager.notification import get_latest_notifications
from manager.db import close_db
from manager.log import get_log
from manager.reporter import registry

bp = Blueprint('dashboard', __name__)

# ---------------------------------------------------------------------------
#                                                          DATABASE HELPERS
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
#                                                                   HELPERS
# ---------------------------------------------------------------------------

def notification_handler_todo(notification):
  get_log().debug("Notification handler TODO: %s", notification)

# notification handler map
notification_handler = {
  'TODO': notification_handler_todo
}

# ---------------------------------------------------------------------------
#                                                                     ROUTES
# ---------------------------------------------------------------------------

# This is the user dashboard
@bp.route('/')
@login_required
def index():

  # redirect admin to admin dashboard if that's the view they want
  if session.get('admin_view'):
    return redirect(url_for('admin.admin'))
  return render_template('dashboard/index.html', reports=registry.descriptions)

# this is for getting at the user dashboard if you're an admin
@bp.route('/user')
@login_required
def user_view_redirect():

  if session.get('admin'):
    session['admin_view'] = False
  return redirect(url_for('dashboard.index'))

@bp.route('/notifications')
@login_required
def stream_notifications():

  # parse options from request arguments
  poll_max = request.args.get('poll_count', None)
  poll_frequency = int(request.args.get('poll_frequency', 1))
  get_log().debug(
    "Polling for notifications every %ds, max polls %s",
    poll_frequency, poll_max)

  # generator for notifications stream
  def eventStream(max, frequency):

    # find end of notifications
    last_notifications = get_latest_notifications()
    if last_notifications:
      last_notification = last_notifications[0].id
    else:
      last_notification = 0

    # loop to stream new notifications
    count = 0
    while not max or count < int(max):

      count += 1
      sleep(frequency)
      notifications = get_latest_notifications(last_notification)

      if notifications:
        get_log().debug("There are %d notifications", len(notifications))

        for notification in notifications:

          # if this notification is directed at you
          # or directed at everybody and not from you
          if (notification.recipient == session['cci']
              or notification.recipient is None and notification.sender != session['cci']):

            # TODO: deal with notification type
            # use some sort of callback, that'd be useful
            try:
              notification_handler[notification.data['strref']](notification)
            except KeyError:
              get_log().error("Unhandled notification message: '%s'", notification.data)
              yield "data: {}\n\n".format(notification.data)

        last_notification = notifications[0].id

      # avoid hung connections by closing between checks
      close_db()

  return Response(stream_with_context(eventStream(poll_max, poll_frequency)), mimetype='text/event-stream')
