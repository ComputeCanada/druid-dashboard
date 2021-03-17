# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=W0613
#
import os
import logging
import configparser
from json import JSONEncoder
from flask import Flask, request, session
from flask_babel import Babel

# utilities
from . import log
from . import db
from . import ldap
from . import otrs

# blueprints
from . import admin
from . import auth
from . import dashboard
from . import api
from . import ajax
from . import status

# misc
from . import errors

# this is so that the notifiers are registered
from . import notifier_slack

# override default JSON encoder to look for `serializable` method
def json_encoder_override(self, obj):
  return getattr(
    obj.__class__,
    "serialize",
    json_encoder_override.default
  )(obj)
json_encoder_override.default = JSONEncoder().default
JSONEncoder.default = json_encoder_override

# languages are not configurable
SUPPORTED_LANGUAGES = ['en', 'fr']

# declare Babel object to be initialized in factory
babel = Babel()

# static defaults
defaults = {
  'APPLICATION_TAG': 'beam',
  'SECRET_KEY': 'dev',
  'LDAP_URI': 'ldap://localhost',
  'LDAP_BINDDN': '',
  'LDAP_PASSWORD': '',
  'LDAP_SKIP_TLS': False,
  'OTRS_QUEUE': 'Test'
}

# optional that may appear in environment or configuration
optionals = [
  'SYSLOG_SERVER',
  'SYSLOG_PORT',
  'SYSLOG_PROTOCOL'
]

def determine_config(default_config_file, default_config, test_config=None):
  """
  Given hardcoded defaults, a config file, and possibly a test config, as well
  as what may be defined in the environment, determine the active
  configuration to be used in this instance.

  Configuration is determined by merging key-value pairs over those defined
  earlier, in the following order: default_config, contents of the config
  file, the test_config, and finally environment variables.

  The following keys are equivalent:
    * the environment variable `BEAM_LDAP_URI`
    * the config map variable `LDAP_URI`
    * the variable defined as `uri` in the `[ldap]` section of the config file

  Args:
    default_config_file (str): configuration file to use by default if
      `BEAM_CONFIG` is not defined in the environment
    default_config (map): key-value pairs of default values
    test_config (map): key-value pairs of configuration set for testing

  Returns:
    map: key-value pairs to be used as configuration, where keys are in
      uppercase for compatibility with Flask.
  """

  # get configuration file from test config or environment
  config_file = default_config_file
  if test_config:
    config_file = test_config.get('CONFIG', config_file)
  config_file = os.environ.get('BEAM_CONFIG', config_file)

  # get parser.  Turn interpolation off so '%' doesn't have to be escaped (in
  # the AMQP URI definition).
  config_from_file = configparser.ConfigParser(delimiters='=', interpolation=None)

  # read configuration
  config_from_file.read(config_file)

  # flag if configuration specified but not found
  if 'BEAM_CONFIG' in os.environ and not config_from_file:
    logging.error(
      "Configuration file '%s' specified but cannot be read",
      os.environ['BEAM_CONFIG']
    )

  # copy defaults
  config = default_config.copy()

  # copy in anything from the configuration
  for section in config_from_file:

    # determine environment and config variable prefixes
    if section != 'DEFAULT':
      configprefix = section.upper() + '_'
    else:
      configprefix = ''

    # loop through configurations
    for key in config_from_file[section]:
      config[configprefix + key.upper()] = config_from_file[section][key]

  # merge in anything from the test configuration
  if test_config:
    config.update(test_config)

  # override with environment variables
  for key in config.keys():
    envvar = 'BEAM_' + key.upper()
    if envvar in os.environ:
      config[key] = os.environ[envvar]

  # also check for optional configurations that have no defaults and may not
  # have been specified in configuration
  for key in optionals:
    envvar = 'BEAM_' + key
    if envvar in os.environ:
      config[key] = os.environ[envvar]

  # interpret boolean values
  for key in ['LDAP_SKIP_TLS']:
    if isinstance(config[key], bool):
      continue
    if config[key].lower() in ['true', 'yes', '1']:
      config[key] = True
    else:
      config[key] = False

  return config

def create_app(test_config=None):

  # create Flask app object
  app = Flask(__name__, instance_relative_config=True)

  # initialize Babel
  babel.init_app(app)

  # determine default database URI based on instance location
  defaults['DATABASE_URI'] = "file:///%s/%s.sqlite" % (
    app.instance_path, __name__)

  # determine default config file
  default_conf = "%s/%s.conf" % (app.instance_path, __name__)

  # load configuration
  config = determine_config(default_conf, defaults, test_config)

  # load the instance config
  app.config.from_mapping(config)

  # ensure the instance folder exists if using SQLite
  if app.config['DATABASE_URI'].startswith('file:'):
    try:
      os.makedirs(app.instance_path)
    except OSError:
      pass

  init_app(app)

  app.register_blueprint(auth.bp)

  app.register_blueprint(dashboard.bp)
  app.add_url_rule('/', endpoint='index')

  app.register_blueprint(admin.bp)
  app.register_blueprint(api.bp)
  app.register_blueprint(ajax.bp)
  app.register_blueprint(status.bp)

  # this is to make get_locale() available to templates
  app.jinja_env.globals.update(get_locale=get_locale)

  # register error handlers
  app.register_error_handler(400, errors.error_400)
  app.register_error_handler(403, errors.error_403)
  app.register_error_handler(404, errors.error_404)
  app.register_error_handler(500, errors.error_500)

  # register generic error handler, unless testing
  if (not app.config.get('TESTING', False)
      and app.config.get('CATCH_ALL_EXCEPTIONS', True)):
    app.register_error_handler(Exception, errors.generic_exception)

  return app


def init_app(app):
  app.teardown_appcontext(db.close_db)
  app.teardown_appcontext(ldap.close_ldap)
  app.teardown_appcontext(log.close_log)
  app.cli.add_command(db.init_db_command)
  app.cli.add_command(db.seed_db_command)
  app.cli.add_command(db.upgrade_db_command)


@babel.localeselector
def get_locale():
  return request.accept_languages.best_match(SUPPORTED_LANGUAGES)
