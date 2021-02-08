# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=W0621,wildcard-import,unused-wildcard-import
#
import os
import tempfile
import pytest
from tests_cli import *
from tests_status import *
from tests_app import *
from tests_apikeys import *
from tests_api import *
from tests_authentication import *
from tests_components import *
from tests_dashboard import *
from tests.ldapstub import LdapStub
from manager import create_app
from manager.db import init_db, seed_db, upgrade_schema

upgrade_versions = os.environ['SCHEMA_VERSIONS'].split(',')
sql_base_dir = os.environ['SCHEMA_BASEDIR']

@pytest.fixture(scope='module', params=upgrade_versions)
def seeded_app(request):

  version = request.param

  # parametrize the stuff
  (sqlite_fh, sqlite_fn) = tempfile.mkstemp()
  uri = 'file://' + sqlite_fn
  schema = '{}/schema-{}.sql'.format(sql_base_dir, version)
  seed = '{}/seed-{}.sql'.format(sql_base_dir, version)

  app = create_app({
    'TESTING': True,
    'DATABASE_URI': uri,
    'CONFIG': 'tests/app.conf',
    'LDAP_STUB': LdapStub()
  })

  with app.app_context():
    init_db(schema)
    seed_db(seed)
    upgrade_schema()

  yield app

  try:
    os.close(sqlite_fh)
    os.unlink(sqlite_fn)
  except OSError:
    # TODO: figure out why this was already closed/unlinked
    pass


@pytest.fixture(scope='module', params=upgrade_versions)
def empty_app(request):

  version = request.param

  # parametrize the stuff
  (sqlite_fh, sqlite_fn) = tempfile.mkstemp()
  uri = 'file://' + sqlite_fn
  schema = '{}/schema-{}.sql'.format(sql_base_dir, version)

  app = create_app({
    'TESTING': True,
    'DATABASE_URI': uri,
    'CONFIG': 'tests/app.conf',
    'LDAP_STUB': LdapStub()
  })

  with app.app_context():
    init_db(schema)
    upgrade_schema()

  yield app

  try:
    os.close(sqlite_fh)
    os.unlink(sqlite_fn)
  except OSError:
    # TODO: figure out why this was already closed/unlinked
    pass
