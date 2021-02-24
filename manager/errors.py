# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=W0613
#
import sys
import traceback
from flask import render_template
from manager.log import get_log


def generic_exception(exception):

  # navigate traceback
  tb = exception.__traceback__
  while tb.tb_next:
    tb = tb.tb_next

  get_log().fatal(
    "Uncaught exception (%s): '%s' occurred in: %s::%s():%d",
    sys.exc_info()[0].__name__,
    exception,
    tb.tb_frame.f_code.co_filename,
    tb.tb_frame.f_code.co_name,
    tb.tb_lineno)

  # send traceback to debug only
  get_log().debug("Traceback: %s", traceback.format_tb(sys.exc_info()[2]))
  return render_template('500.html'), 500

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
