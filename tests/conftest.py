# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=W0621
#
import os
import tempfile
import pytest
from ldapstub import LdapStub
from app import create_app
from app.db import get_db, init_db, seed_db


(sqlite_fh, sqlite_fn) = tempfile.mkstemp()
sqlite_params = {
  'schema': 'schema.sql',
  'seed': '../tests/data.sql',
  'uri': 'file://' + sqlite_fn,
  'delete_afterwards': True,
  'filehandle': sqlite_fh,
  'filename': sqlite_fn
}
pgsql_params = {
  'schema': 'schema.psql',
  'seed': '../tests/data.sql',
  'uri': os.environ.get('BEAM_PGSQL_URI', 'postgresql://postgres:supersecretpassword@localhost:5432/postgres')
}

@pytest.fixture(scope='module', params=[sqlite_params], ids=['sqlite'])
#@pytest.fixture(scope='module', params=[pgsql_params], ids=['pgsql'])
#@pytest.fixture(scope='module', params=[sqlite_params, pgsql_params], ids=['sqlite', 'pgsql'])
def app(request):

  app = create_app({
    'TESTING': True,
    'DATABASE_URI': request.param['uri'],
    'CONFIG': 'tests/app.conf',
    'LDAP_STUB': LdapStub()
  })

  with app.app_context():
    init_db()
    seed_db(request.param['seed'])
    get_db().commit()

  yield app

  if request.param.get('delete_afterwards', False):
    try:
      os.close(request.param['filehandle'])
    except OSError:
      # TODO: figure out why this was already closed
      pass
    os.unlink(request.param['filename'])


@pytest.fixture(scope='class')
def client(app):
  return app.test_client()


@pytest.fixture(scope='module', params=[sqlite_params, pgsql_params], ids=['sqlite', 'pgsql'])
def empty_app(request):

  app = create_app({
    'TESTING': True,
    'DATABASE_URI': request.param['uri'],
    'CONFIG': 'tests/app.conf'
  })

  with app.app_context():
    init_db()

    # this fixture is for testing a brand-new auction site or one with no
    # current activity, but minimal seeding is still required, such as for
    # testing API keys
    get_db().execute("""
      INSERT INTO apikeys (access, secret)
      VALUES ('testapikey', 'WuHheVDysQQwdb+NK98w8EOHdiNUjLlz2Uxg/kIHqIGOek4DAmC5NCd2gZv7RQ==')
    """)
    get_db().commit()

  yield app

  print(request.param['uri'])
  if request.param.get('delete_afterwards', False):
    #os.close(request.param['filehandle'])
    os.unlink(request.param['filename'])


@pytest.fixture(scope='module')
def empty_client(empty_app):
  return empty_app.test_client()


@pytest.fixture
def runner(app):
  return app.test_cli_runner()
