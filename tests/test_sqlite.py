# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=W0621,wildcard-import,unused-wildcard-import
#
import os
import tempfile
import pytest
from tests_05_clusters import *
from tests_10_components import *
from tests_15_apikeys import *
from tests_20_api import *
from tests_cli import *
from tests_status import *
from tests_app import *
from tests_authentication import *
from tests_bursts import *
from tests_oldjobs import *
from tests_dashboard import *
from tests.ldapstub import LdapStub
from tests.otrsstub import OtrsStub
from manager import create_app
from manager.db import get_db, init_db, seed_db
from manager.notifier import clear_notifiers

# common test params; this was more useful when both SQLite and Postgres
# were handled in the same test setup module
test_params = [{
  'schema': 'schema.sql',
  'seed': '../tests/data.sql',
  'delete_afterwards': True,
}]
test_ids = ['sqlite']


@pytest.fixture(scope='module', params=test_params, ids=test_ids)
def seeded_app(request):

  (filehandle, filename) = tempfile.mkstemp()
  uri = 'file://' + filename

  app = create_app({
    'TESTING': True,
    'DATABASE_URI': uri,
    'CONFIG': 'tests/app.conf',
    'LDAP_STUB': LdapStub(),
    'OTRS_STUB': OtrsStub()
  })

  with app.app_context():
    init_db()
    seed_db(request.param['seed'])
    get_db().commit()
    clear_notifiers()

  yield app

  if request.param.get('delete_afterwards', False):
    os.close(filehandle)
    os.unlink(filename)


@pytest.fixture(scope='module', params=test_params, ids=test_ids)
def empty_app(request):

  (filehandle, filename) = tempfile.mkstemp()
  uri = 'file://' + filename

  app = create_app({
    'TESTING': True,
    'DATABASE_URI': uri,
    'CONFIG': 'tests/app.conf',
    'LDAP_STUB': LdapStub(),
    'OTRS_STUB': OtrsStub()
  })

  with app.app_context():
    init_db()

    # this fixture is for testing a brand-new instance with no current
    # activity, but minimal seeding is still required, such as for testing
    # API keys
    get_db().execute("""
      INSERT INTO apikeys (access, secret, component)
      VALUES ('testapikey', 'WuHheVDysQQwdb+NK98w8EOHdiNUjLlz2Uxg/kIHqIGOek4DAmC5NCd2gZv7RQ==', 'testcluster_detector')
    """)
    get_db().commit()

  yield app

  if request.param.get('delete_afterwards', False):
    os.close(filehandle)
    os.unlink(filename)
