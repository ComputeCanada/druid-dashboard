# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=W0613
#
from flask import render_template

# bad request
def error_400(e):
  return render_template('400.html'), 400

# forbidden
def error_403(e):
  return render_template('403.html'), 403

# not found
def error_404(e):
  return render_template('404.html'), 404

# we done mucked up
def error_500(e):
  return render_template('500.html'), 500
