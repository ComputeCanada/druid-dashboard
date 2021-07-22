# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=W0613
#
import sys
import traceback
from flask import render_template, jsonify
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

# ---------------------------------------------------------------------------
#                                         Error response templates
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
#                                         Response wrappers for REST calls
# See RFC 7807 (https://datatracker.ietf.org/doc/html/rfc7807)
# ---------------------------------------------------------------------------

def xhr_response(status, msg, *args, title=None):
  response = { 'status': status }
  if msg:
    response['detail'] = msg % args
  if title:
    response['title'] = title
  return jsonify(response), status

def xhr_error(status, msg, *args, title=None):
  response = { 'status': status }
  if msg:
    if args:
      #get_log().error(msg, args)
      response['detail'] = msg % args
    else:
      get_log().error(msg)
      response['detail'] = msg
  if title:
    response['title'] = title
  return jsonify(response), status
  # TODO: figure out why I couldn't swap the above with:
  #return xhr_response(status, msg, args, title)
  # ...it's something to do about args being reinterpreted or augmented

def xhr_success(status=200, title=None):
  response = { 'status': status }
  if title:
    response['title'] = title
  return jsonify(response), status
