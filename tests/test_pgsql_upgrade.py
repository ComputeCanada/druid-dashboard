# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=W0621,wildcard-import,unused-wildcard-import
#
import os
import random
import string
import pytest
import psycopg2
from tests_clusters import *
from tests_components import *
from tests_apikeys import *
from tests_api import *
from tests_cli import *
from tests_status import *
from tests_app import *
from tests_authentication import *
from tests_bursts import *
from tests_oldjobs import *
from tests_otrs import *
from tests_dashboard import *
from ldapstub import LdapStub
from otrsstub import OtrsStub
from tests_upgrades import *
from conftest import find_seed_update_scripts
from manager import create_app
from manager.db import init_db, seed_db, upgrade_schema, SCHEMA_VERSION
from manager.notifier import clear_notifiers

def random_database_name():
  return 'testing_' + ''.join(random.choices(string.ascii_lowercase + string.digits, k = 8))

upgrade_versions = os.environ['SCHEMA_VERSIONS'].split(',')
if SCHEMA_VERSION in upgrade_versions:
  del upgrade_versions[-1]
sql_base_dir = os.environ['SCHEMA_BASEDIR']
seed_dir = os.environ.get('SEED_DIR', '../tests')
uri = os.environ.get('BEAM_PGSQL_URI', 'postgresql://postgres:supersecretpassword@localhost:5432/postgres')

@pytest.fixture(scope='class', params=upgrade_versions)
def unupgraded_app(request):

  # create random database
  dbname = random_database_name()
  pgconn = psycopg2.connect(uri)
  pgconn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
  pgconn.cursor().execute("CREATE DATABASE {}".format(dbname))

  tempuri = 'postgresql://postgres:supersecretpassword@localhost:5432/{}'.format(dbname)

  version = request.param

  # parametrize the stuff
  schema = '{}/schema-{}.psql'.format(sql_base_dir, version)
  seed = '{}/data-{}.sql'.format(seed_dir, version)

  app = create_app({
    'TESTING': True,
    'DATABASE_URI': tempuri,
    'CONFIG': 'tests/app.conf',
    'LDAP_STUB': LdapStub(),
    'OTRS_STUB': OtrsStub()
  })

  with app.app_context():
    init_db(schema)
    seed_db(seed)

  yield app

  pgconn.cursor().execute("DROP DATABASE {}".format(dbname))
  pgconn.close()

# this needs to be defined here because it's not common to non-upgrade contexts
@pytest.fixture(scope='class')
def unupgraded_client(unupgraded_app):
  return unupgraded_app.test_client()

@pytest.fixture(scope='class', params=upgrade_versions)
def seeded_app(request):

  # create random database
  dbname = random_database_name()
  pgconn = psycopg2.connect(uri)
  pgconn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
  pgconn.cursor().execute("CREATE DATABASE {}".format(dbname))

  tempuri = 'postgresql://postgres:supersecretpassword@localhost:5432/{}'.format(dbname)

  version = request.param

  # parametrize the stuff
  schema = '{}/schema-{}.psql'.format(sql_base_dir, version)
  seed = '{}/data-{}.sql'.format(seed_dir, version)

  app = create_app({
    'TESTING': True,
    'DATABASE_URI': tempuri,
    'CONFIG': 'tests/app.conf',
    'LDAP_STUB': LdapStub(),
    'OTRS_STUB': OtrsStub()
  })

  # find updates to seed data which are applied to match updates to test suite
  seed_updates = find_seed_update_scripts(app.root_path, version)

  with app.app_context():
    init_db(schema)
    seed_db(seed)
    upgrade_schema(seed_updates)
    clear_notifiers()

  yield app

  pgconn.cursor().execute("DROP DATABASE {}".format(dbname))
  pgconn.close()


@pytest.fixture(scope='class', params=upgrade_versions)
def empty_app(request):

  # create random database
  dbname = random_database_name()
  pgconn = psycopg2.connect(uri)
  pgconn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
  pgconn.cursor().execute("CREATE DATABASE {}".format(dbname))

  tempuri = 'postgresql://postgres:supersecretpassword@localhost:5432/{}'.format(dbname)

  version = request.param

  # parametrize the stuff
  schema = '{}/schema-{}.psql'.format(sql_base_dir, version)

  app = create_app({
    'TESTING': True,
    'DATABASE_URI': tempuri,
    'CONFIG': 'tests/app.conf'
  })

  with app.app_context():
    init_db(schema)
    upgrade_schema()

  yield app

  pgconn.cursor().execute("DROP DATABASE {}".format(dbname))
  pgconn.close()
