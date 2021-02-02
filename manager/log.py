# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
import logging
from flask import g

def get_log():
  if 'logger' not in g:
    # initialize logging
    # this should be on a formatter attached to a handler but simple for now
    logging.basicConfig(format='%(asctime)s %(levelname)7s %(message)s',
                        datefmt='%Y%m%d.%H%M%S',
                        level=logging.DEBUG)
    g.logger = logging.getLogger()

    g.logger.debug("Initializing logger")

  return g.logger

def close_log(e=None):
  logger = g.pop('logger', None)
  if logger:
    if e:
      logger.info("Closing logger in presence of error condition: '%s'", e)
    else:
      logger.debug("Closing down logger")

  # actually nothing to close
