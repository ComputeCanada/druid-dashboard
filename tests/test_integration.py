# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=W0621,wildcard-import,unused-wildcard-import
#
import os
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
from tests.otrsstub import OtrsStub
from manager import create_app
from manager.db import get_db, init_db, seed_db
from manager.notifier import clear_notifiers

test_params = [{
  'schema': 'schema.psql',
  'seed': '../tests/data.sql',
  'uri': os.environ.get('BEAM_PGSQL_URI', 'postgresql://postgres:supersecretpassword@localhost:5432/postgres')
}]
test_ids = ['pgsql']


@pytest.fixture(scope='class', params=test_params, ids=test_ids)
def seeded_app(request):

  app = create_app({
    'TESTING': True,
    'DATABASE_URI': request.param['uri'],
    'CONFIG': 'tests/app.conf',
    'LDAP_URI': 'ldap://localhost',
    'OTRS_STUB': OtrsStub()
  })

  with app.app_context():
    init_db()
    seed_db(request.param['seed'])
    get_db().commit()
    clear_notifiers()

  yield app


@pytest.fixture(scope='class', params=test_params, ids=test_ids)
def empty_app(request):

  app = create_app({
    'TESTING': True,
    'DATABASE_URI': request.param['uri'],
    'CONFIG': 'tests/app.conf',
    'LDAP_URI': 'ldap://localhost',
    'OTRS_STUB': OtrsStub()
  })

  with app.app_context():
    init_db()

  yield app

  print(request.param['uri'])
  if request.param.get('delete_afterwards', False):
    #os.close(request.param['filehandle'])
    os.unlink(request.param['filename'])
