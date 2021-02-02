# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#

from flask import Blueprint, render_template

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

# This is the admin dashboard
@bp.route('/')
@admin_required
def admin():

  # TODO: load authorizations from Grouper
  # TODO: load API keys
  # TODO: load site configuration
  # TODO: decide whether to do the above and also use AJAX, or skip and just
  #       do AJAX

  return render_template('admin/index.html')
