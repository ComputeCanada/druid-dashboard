# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=C0415
#
import os
from enum import Enum
import re
import click
from flask import current_app, g
from flask.cli import with_appcontext
from manager.log import get_log
from manager import exceptions


# Current database schema version
# format is integer, YYYYMMDD[.R] where R is an arbitrary digit in the case of
# multiple releases in day.
#
# This number must match the latest entry in the database's schemalog table,
# or an upgrade should be performed.
SCHEMA_VERSION = 20201209

# query to fetch latest schema version
SQL_GET_SCHEMA_VERSION = """
  SELECT    version
  FROM      schemalog
  ORDER BY  applied DESC
  LIMIT     1
"""

# scripts path
SQL_SCRIPTS_DIR = 'sql'

# This is used to queue custom DB-ready classes for to be registered for use
# with specific databases, once the appropriate database is identified and
# initialized.
_register_adapters_for = []
def queue_adapter_registration(cls):
  _register_adapters_for.append(cls)


def get_db():
  """
  Retrieve application's database object, initializing if necessary.
  """

  if 'db' not in g:
    g.db = open_db(current_app.config['DATABASE_URI'])

  return g.db


def open_db(uri):
  """
  Open database connection for appropriate database type based on URI and
  return the connection handle.
  """
  scheme = uri.split(':', 1)[0]

  if scheme == 'file':
    from manager.db_sqlite import open_db_sqlite, register_adapter
    db = open_db_sqlite(uri)

  elif scheme == 'postgresql':
    from manager.db_postgres import open_db_postgres, register_adapter
    db = open_db_postgres(uri)

  else:
    raise exceptions.UnsupportedDatabase(scheme)

  # register adapter(s) for bespoke classes
  for cls in _register_adapters_for:
    register_adapter(cls)

  return db


def close_db(e=None):
  db = g.pop('db', None)

  if e:
    get_log().info("Closing database in presence of error condition: '%s'", e)

  if db is not None:
    db.close()


def init_db():
  db = get_db()

  if db.type == 'sqlite':
    schema = "{}/schema.sql".format(SQL_SCRIPTS_DIR)
  elif db.type == 'postgres':
    schema = "{}/schema.psql".format(SQL_SCRIPTS_DIR)

  with current_app.open_resource(schema) as f:
    db.executescript(f.read().decode('utf8'))


def seed_db(seedfile):
  db = get_db()

  with current_app.open_resource(seedfile) as f:
    db.executescript(f.read().decode('utf8'))


def get_schema_version():
  db = get_db()
  try:
    vers = db.execute(SQL_GET_SCHEMA_VERSION).fetchone()['version']
  except Exception as e:
    get_log().error("Error in retrieving schema version: {}".format(e))
    raise exceptions.DatabaseException("Could not retrieve schema version") from e
  if not vers:
    get_log().error("Could not find latest schema version")
    raise exceptions.DatabaseException("Could not determine schema version")
  return (vers, SCHEMA_VERSION)


def upgrade_schema():
  (actual, expected) = get_schema_version()
  if actual == expected:
    # trivial: actual matches expected, no action needed
    return (actual, expected, None)

  ## Find upgrade path.  Scripts are "${from}_to_${to}.[sql|psql]".  Might need
  ## to run several, such as if there is ${from}_to_int1.sql, int1_to_${to}.sql
  ## for example.

  ## Build dictionary of upgrade scripts keyed on their starting versions.
  ## Values are the ending version and the filename.
  scriptdict = {}

  # build regular expression for matching upgrade scripts
  db = get_db()
  if db.type == 'sqlite':
    ext = 'sql'
  elif db.type == 'postgres':
    ext = 'psql'
  regex = re.compile(r'^([^_]+)_to_([^_]+).' + ext)

  # iterate through each file and if it's an update script add it to dict
  # pylint: disable=unused-variable
  for root, dirs, files in os.walk(SQL_SCRIPTS_DIR):
    for file in files:
      print(file)
      m = regex.match(file)
      if m:
        if m[1] in scriptdict:
          # this should not happen
          # TODO: proper exception
          raise Exception("This should not have happened.  Also this is a bad exception")
        scriptdict[m[1]] = (m[2], file)

  # find path through upgrades from actual to expected
  have_upgrade_path = False
  upgrade_path = []
  current = actual
  while current in scriptdict:
    if len(scriptdict[current]) == 1:
      upgrade_path.append(scriptdict[current][1])
      current = scriptdict[current][0]
      if current == expected:
        have_upgrade_path = True
        break

  if not have_upgrade_path:
    # this is a pretty serious application error
    # TODO: proper exception
    raise Exception("There is no upgrade path from the existing schema to the expected version.")

  # run through upgrade scripts
  actions = []
  for upgrade in upgrade_path:
    with current_app.open_resource(upgrade) as f:
      get_log.info("Upgrading DB: %s...", upgrade)
      db.executescript(f.read().decode('utf8'))
      actions.append("Executed {}".format(upgrade))
  get_log.info("Upgraded DB.")

  return (actual, expected, actions)

@click.command('init-db')
@with_appcontext
def init_db_command():
  """Clear the existing data and create new tables."""
  init_db()
  click.echo('Initialized the database.')


@click.command('seed-db')
@click.argument('seedfile')
@with_appcontext
def seed_db_command(seedfile):
  """Clear existing data, create new tables, seed with test data."""

  init_db()
  seed_db(seedfile)
  click.echo('Initialized and seeded the database.')


class DbEnum(Enum):

  # pylint: disable=W0613
  def __init__(self, *args):
    cls = self.__class__
    # pylint: disable=W0143
    if any(self.value == e.value for e in cls):
      a = self.name
      e = cls(self.value).name
      raise ValueError("Values must be unique: %r -> %r" % (a, e))

    queue_adapter_registration(cls)

  def getquoted(self):
    return str.encode("'" + self.value + "'")

  def __str__(self):
    return str(self.value)

  # return serializable representation for JSON encoder
  def serializable(self):
    return self.__str__()
