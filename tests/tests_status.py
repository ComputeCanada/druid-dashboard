# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
from manager.db import SCHEMA_VERSION

# ---------------------------------------------------------------------------
#                                                                STATUS
# ---------------------------------------------------------------------------

def test_status(client):
  """
  Test that /status returns a 200 in the case of things working, which they
  should be here because it's stubbed out.
  """
  response = client.get('/status/')
  assert response.data == 'LDAP: Okay\nDB: Okay (schema version {})'.format(SCHEMA_VERSION).encode('utf-8')
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
