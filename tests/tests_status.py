# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
from manager.db import SCHEMA_VERSION

# ---------------------------------------------------------------------------
#                                                                STATUS
# ---------------------------------------------------------------------------

def test_status(client):
  """
  Test that /status returns a 200 in the case of the app responding.
  """
  response = client.get('/status/')
  print(response.data)
  assert response.data == "I'm: Okay".encode('utf-8')
  assert response.status_code == 200

def test_services_status_db(client):
  """
  Test that /status/services returns a 200 in the case of things working,
  which they should be here because they're stubbed out.
  """
  response = client.get('/status/services/db')
  print(response.data)
  assert response.data == 'DB: Okay (schema version {})'.format(SCHEMA_VERSION).encode('utf-8')
  assert response.status_code == 200

def test_services_status_ldap(client):
  """
  Test that /status/services returns a 200 in the case of things working,
  which they should be here because they're stubbed out.
  """
  response = client.get('/status/services/ldap')
  print(response.data)
  assert response.data == 'LDAP: Okay'.encode('utf-8')
  assert response.status_code == 200

def test_services_status_otrs(client):
  """
  Test that /status/services returns a 200 in the case of things working,
  which they should be here because they're stubbed out.
  """
  response = client.get('/status/services/otrs')
  print(response.data)
  assert response.data == 'OTRS: Okay'.encode('utf-8')
  assert response.status_code == 200

def test_services_status(client):
  """
  Test that /status/services returns a 200 in the case of things working,
  which they should be here because they're stubbed out.
  """
  response = client.get('/status/services')
  print(response.data)
  assert response.data == 'LDAP: Okay\nDB: Okay (schema version {})\nOTRS: Okay'.format(SCHEMA_VERSION).encode('utf-8')
  assert response.status_code == 200

def test_update_db(client):
  """
  Test that database status correctly reports that the schema in the DB and
  in the code match.
  """
  response = client.get('/status/db')
  print(response.data)
  expected = 'DB schema at %s, code schema at %s, no action taken' % (SCHEMA_VERSION, SCHEMA_VERSION)
  assert response.data == expected.encode('utf-8')
  assert response.status_code == 200
