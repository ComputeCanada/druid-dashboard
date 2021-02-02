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
  assert response.status_code == 200
  assert response.data == 'LDAP: Okay\nDB: Okay (schema version {})'.format(SCHEMA_VERSION).encode('utf-8')
