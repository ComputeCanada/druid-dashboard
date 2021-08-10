# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#

from flask import Blueprint, render_template, session

from manager.auth import admin_required

bp = Blueprint('admin', __name__, url_prefix='/admin')

# ---------------------------------------------------------------------------
#                                                          DATABASE HELPERS
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
#                                                                   HELPERS
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
#                                                                     ROUTES
# ---------------------------------------------------------------------------

# This is the admin dashboard.  Everything is loaded through AJAX
@bp.route('/')
@admin_required
def admin():

  # remember to come back to admin view
  session['admin_view'] = True

  return render_template('admin/index.html')
