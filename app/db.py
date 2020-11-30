# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=C0415
#
from enum import Enum
import click
from flask import current_app, g
from flask.cli import with_appcontext
from app.log import get_log
from app import exceptions


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
    from .db_sqlite import open_db_sqlite, register_adapter
    db = open_db_sqlite(uri)

  elif scheme == 'postgresql':
    from .db_postgres import open_db_postgres, register_adapter
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
    schema = "schema.sql"
  elif db.type == 'postgres':
    schema = "schema.psql"

  with current_app.open_resource(schema) as f:
    db.executescript(f.read().decode('utf8'))


def seed_db():
  db = get_db()

  if db.type == 'sqlite':
    seedfile = 'seed.sql'
  elif db.type == 'postgres':
    seedfile = 'seed.psql'

  with current_app.open_resource(seedfile) as f:
    db.executescript(f.read().decode('utf8'))


@click.command('init-db')
@with_appcontext
def init_db_command():
  """Clear the existing data and create new tables."""
  init_db()
  click.echo('Initialized the database.')


@click.command('seed-db')
@with_appcontext
def seed_db_command():
  """Clear existing data, create new tables, seed with test data."""

  init_db()
  seed_db()
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
