# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
import re
from manager.db import SCHEMA_VERSION

# ---------------------------------------------------------------------------
#                                                                STATUS
# ---------------------------------------------------------------------------

def test_update_db_unupgraded(unupgraded_client):
  """
  Test that database status correctly reports that the schema in the DB and
  in the code don't match.
  """
  response = unupgraded_client.get('/status/db')
  print(response.data)

  # not really sure what the upgrade paths are unless I hardcoded them here,
  # so just want to ensure the last action (listed last) upgrades to the
  # latest version.
  upgrades = response.data.decode('utf-8').split('\n')
  assert re.search(r'DB required upgrade from \w+ to ' + SCHEMA_VERSION, upgrades[0], re.DOTALL) is not None
  assert re.search(r'Executed \S+/manager/sql/\S+_to_{}\.p?sql'.format(SCHEMA_VERSION), upgrades[-1], re.DOTALL)
  assert response.status_code == 200
