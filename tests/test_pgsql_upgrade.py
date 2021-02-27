# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=W0621,wildcard-import,unused-wildcard-import
#
import os
import random
import string
import pytest
import psycopg2
from tests_cli import *
from tests_status import *
from tests_app import *
from tests_apikeys import *
from tests_api import *
from tests_authentication import *
from tests_components import *
from tests_dashboard import *
from tests_upgrades import *
from ldapstub import LdapStub
from manager import create_app
from manager.db import get_db, init_db, seed_db, upgrade_schema, SCHEMA_VERSION

def random_database_name():
  return 'tmp_' + ''.join(random.choices(string.ascii_lowercase + string.digits, k = 8))

upgrade_versions = os.environ['SCHEMA_VERSIONS'].split(',')
if SCHEMA_VERSION in upgrade_versions:
  del upgrade_versions[-1]
sql_base_dir = os.environ['SCHEMA_BASEDIR']
uri = os.environ.get('BEAM_PGSQL_URI', 'postgresql://postgres:supersecretpassword@localhost:5432/postgres')

@pytest.fixture(scope='module', params=upgrade_versions)
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
  seed = '{}/seed-{}.sql'.format(sql_base_dir, version)

  app = create_app({
    'TESTING': True,
    'DATABASE_URI': tempuri,
    'CONFIG': 'tests/app.conf',
    'LDAP_STUB': LdapStub()
  })

  with app.app_context():
    init_db(schema)
    seed_db(seed)

  yield app

  pgconn.cursor().execute("DROP DATABASE {}".format(dbname))
  pgconn.close()

# this needs to be defined here because it's not common to non-upgrade contexts
@pytest.fixture(scope='module')
def unupgraded_client(unupgraded_app):
  return unupgraded_app.test_client()

@pytest.fixture(scope='module', params=upgrade_versions)
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
  seed = '{}/seed-{}.sql'.format(sql_base_dir, version)

  app = create_app({
    'TESTING': True,
    'DATABASE_URI': tempuri,
    'CONFIG': 'tests/app.conf',
    'LDAP_STUB': LdapStub()
  })

  with app.app_context():
    init_db(schema)
    seed_db(seed)
    upgrade_schema()

  yield app

  pgconn.cursor().execute("DROP DATABASE {}".format(dbname))
  pgconn.close()


@pytest.fixture(scope='module', params=upgrade_versions)
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

    # this fixture is for testing a brand-new auction site or one with no
    # current activity, but minimal seeding is still required, such as for
    # testing API keys
    get_db().execute("""
      INSERT INTO clusters (id, name) VALUES ('testcluster', 'Test Cluster');
      INSERT INTO components (id, name, cluster, service) VALUES ('testcluster_detector', 'Detector', 'testcluster', 'detector');
      INSERT INTO apikeys (access, secret, component)
      VALUES ('testapikey', 'WuHheVDysQQwdb+NK98w8EOHdiNUjLlz2Uxg/kIHqIGOek4DAmC5NCd2gZv7RQ==', 'testcluster_detector')
    """)
    get_db().commit()

  yield app

  pgconn.cursor().execute("DROP DATABASE {}".format(dbname))
  pgconn.close()
