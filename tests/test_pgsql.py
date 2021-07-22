# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=W0621,wildcard-import,unused-wildcard-import
#
import os
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
from tests_ajax import *
from tests.ldapstub import LdapStub
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


@pytest.fixture(scope='module', params=test_params, ids=test_ids)
def seeded_app(request):

  app = create_app({
    'TESTING': True,
    'DATABASE_URI': request.param['uri'],
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
      INSERT INTO clusters (id, name) VALUES ('testcluster', 'Test Cluster');
      INSERT INTO components (id, name, cluster, service) VALUES ('testcluster_detector', 'Detector', 'testcluster', 'detector');
      INSERT INTO apikeys (access, secret, component)
      VALUES ('testapikey', 'WuHheVDysQQwdb+NK98w8EOHdiNUjLlz2Uxg/kIHqIGOek4DAmC5NCd2gZv7RQ==', 'testcluster_detector')
    """)
    get_db().commit()

  yield app
