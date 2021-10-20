# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=W0621,wildcard-import,unused-wildcard-import
#
import os
import tempfile
import pytest
from tests_otrs import *
from manager import create_app
from manager.db import get_db, init_db, seed_db
from manager.notifier import clear_notifiers

# common test params; this was more useful when both SQLite and Postgres
# were handled in the same test setup module
test_params = [{
  'schema': 'schema.sql',
  'seed': '../tests/selenium-seed.sql',
  'delete_afterwards': True,
}]
test_ids = ['otrs']


@pytest.fixture(scope='module', params=test_params, ids=test_ids)
def seeded_app(request):

  (filehandle, filename) = tempfile.mkstemp()
  uri = 'file://' + filename

  app = create_app({
    'TESTING': True,
    'DATABASE_URI': uri,
    'CONFIG': 'tests/otrs.conf'
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
    'CONFIG': 'tests/otrs.conf'
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
