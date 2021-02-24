# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
import logging
import logging.handlers
import socket
from flask import g, current_app

def get_log():
  if 'logger' not in g:
    # initialize logging
    # this should be on a formatter attached to a handler but simple for now
    logging.basicConfig(format='%(asctime)s %(levelname)7s %(message)s',
                        datefmt='%Y%m%d.%H%M%S',
                        level=logging.DEBUG)
    g.logger = logging.getLogger()

    sl_handler = None
    if 'SYSLOG_SERVER' in current_app.config:
      server = current_app.config['SYSLOG_SERVER']
      port = current_app.config.get('SYSLOG_PORT', 514)
      protocol = current_app.config.get('SYSLOG_PROTOCOL', 'udp').lower()
      try:
        sockit = {
          'udp': socket.SOCK_DGRAM,
          'tcp': socket.SOCK_STREAM
        }[protocol]
        sl_handler = logging.handlers.SysLogHandler(address=(server, port), socktype=sockit)
      except KeyError:
        # TODO: better exception
        # also TODO: this is definitely going to confuse me
        # pylint: disable=raise-missing-from
        logging.error('ConfigError("Bad protocol specified; you suck")')
      else:
        # apparently only affects TCP: messages are not properly parsed with
        # rsyslog if append_nul is True, which is default, and messages don't
        # also include newlines
        if protocol == 'tcp':
          logging.handlers.SysLogHandler.append_nul = False

    elif 'SYSLOG_SOCKET' in current_app.config:
      address = current_app.config['SYSLOG_SOCKET']
      sl_handler = logging.handlers.SysLogHandler(address=address)

    if sl_handler:

      loglevel = current_app.config.get('SYSLOG_LEVEL', 'info').lower()
      sl_handler.setLevel({
        'emerg': logging.handlers.SysLogHandler.LOG_EMERG,
        'panic': logging.handlers.SysLogHandler.LOG_EMERG,
        'crit': logging.handlers.SysLogHandler.LOG_CRIT,
        'critical': logging.handlers.SysLogHandler.LOG_CRIT,
        'alert': logging.handlers.SysLogHandler.LOG_ALERT,
        'err': logging.handlers.SysLogHandler.LOG_ERR,
        'error': logging.handlers.SysLogHandler.LOG_ERR,
        'warn': logging.handlers.SysLogHandler.LOG_WARNING,
        'warning': logging.handlers.SysLogHandler.LOG_WARNING,
        'notice': logging.handlers.SysLogHandler.LOG_NOTICE,
        'info': logging.handlers.SysLogHandler.LOG_INFO,
        'debug': logging.handlers.SysLogHandler.LOG_DEBUG
      }[loglevel])

      tag = current_app.config.get('APPLICATION_TAG', 'myapp')
      sl_formatter = logging.Formatter(tag + ": %(message)s\n")
      sl_handler.setFormatter(sl_formatter)

      g.logger.addHandler(sl_handler)

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
