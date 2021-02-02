# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
from manager.db import init_db_command


# ---------------------------------------------------------------------------
#                                                              CLI commands
# ---------------------------------------------------------------------------

def test_init_db(empty_app):
  runner = empty_app.test_cli_runner()
  result = runner.invoke(init_db_command)
  assert "Initialized the database." in result.output


#def test_seed_db(app):
#  runner = app.test_cli_runner()
#  result = runner.invoke(seed_db_command)
#  assert "Initialized and seeded the database." in result.output


#def test_upgrade_db_none_avail(app):
#  runner = app.test_cli_runner()
#  result = runner.invoke(upgrade_db_command)
#  assert "No upgrades available for schema version 0.1." in result.output
#
#
#def test_import_csv(app):
#  runner = app.test_cli_runner()
#  result = runner.invoke(import_csv_command, ["tests/import-test.csv"])
#  assert str(result) == '<Result okay>'
