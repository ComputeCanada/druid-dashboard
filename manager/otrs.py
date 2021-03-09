# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#

import pyotrs
from flask import g, current_app
from manager.log import get_log
# TODO: use this instead of Exception in get_otrs()--but wasn't
# getting caught
#from requests import HTTPError


def get_otrs():
  """
  Note: Does not throw exception if OTRS cannot be contacted, because app
        should not depend on OTRS being up to function.  So client should
        check whether returned handle is None or not before attempting to
        use it.
  """
  if 'otrs' not in g:
    # get connection config
    try:
      url = current_app.config['OTRS_URL']
      user = current_app.config['OTRS_USERNAME']
      pw = current_app.config['OTRS_PASSWORD']
    except KeyError:
      # TODO: should throw exception; this is a configuration error
      get_log().error("OTRS configuration missing")
      client = None
    else:
      # create OTRS client object
      try:
        get_log().debug("Creating OTRS client session with url=%s, username=%s", url, user)
        client = pyotrs.Client(url, user, pw)

        # recommended but not functional (?)
        #if client.session_restore_or_create():
        if client.session_create():
          get_log().debug("Initialized OTRS client.")
        else:
          # TODO: get information about error?
          get_log().error("Unable to initialize OTRS client.")
          client = None
      #except HTTPError as e:
      except Exception as e:
        get_log().error("Unable to initialize OTRS client: %s", e)
        client = None
    g.otrs = client

  return g.otrs


def close_otrs(e=None):
  if 'otrs' in g:
    if e:
      get_log().info("Closing OTRS client in presence of error")
    else:
      get_log().debug("Closing OTRS client.")
    g.otrs.close()
