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
from app import create_app
from app.db import get_db, init_db, seed_db

(sqlite_fh, sqlite_fn) = tempfile.mkstemp()
test_params = [{
  'schema': 'schema.sql',
  'seed': '../tests/data.sql',
  'uri': 'file://' + sqlite_fn,
  'delete_afterwards': True,
  'filehandle': sqlite_fh,
  'filename': sqlite_fn
}]
test_ids = ['sqlite']


@pytest.fixture(scope='module', params=test_params, ids=test_ids)
def seeded_app(request):

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
      os.unlink(request.param['filename'])
    except OSError:
      # TODO: figure out why this was already closed/unlinked
      pass


@pytest.fixture(scope='module', params=test_params, ids=test_ids)
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
      INSERT INTO apikeys (access, secret, component)
      VALUES ('testapikey', 'WuHheVDysQQwdb+NK98w8EOHdiNUjLlz2Uxg/kIHqIGOek4DAmC5NCd2gZv7RQ==', 'testcluster_detector')
    """)
    get_db().commit()

  yield app

  print(request.param['uri'])
  if request.param.get('delete_afterwards', False):
    #os.close(request.param['filehandle'])
    os.unlink(request.param['filename'])
