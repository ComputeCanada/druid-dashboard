# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=W0621,wildcard-import,unused-wildcard-import
#
import os
import tempfile
import pytest
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


@pytest.fixture(scope='class', params=test_params, ids=test_ids)
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


@pytest.fixture(scope='class', params=test_params, ids=test_ids)
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

  yield app

  if request.param.get('delete_afterwards', False):
    os.close(filehandle)
    os.unlink(filename)
