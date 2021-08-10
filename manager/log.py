# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=global-statement
#
import logging

_logger = None

def get_log():

  global _logger

  if not _logger:
    # initialize logging
    # this should be on a formatter attached to a handler but simple for now
    logging.basicConfig(format='%(asctime)s %(levelname)-7s %(message)s',
                        datefmt='%Y%m%d.%H%M%S',
                        level=logging.DEBUG)
    _logger = logging.getLogger()

    _logger.debug("Initializing logger")

  return _logger

def close_log(e=None):

  global _logger
  if _logger:
    if e:
      _logger.info("Closing logger in presence of error condition: '%s'", e)
    else:
      _logger.debug("Closing down logger")

  # actually nothing to close
