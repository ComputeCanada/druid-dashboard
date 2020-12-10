# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
import pytest
from app import create_app
from app.db import init_db
import app.exceptions


# ---------------------------------------------------------------------------
#                                                          APP
# ---------------------------------------------------------------------------

def test_config():
  assert not create_app().testing
  assert create_app({'TESTING': True}).testing


def test_config_bad_database():
  beam = create_app({'DATABASE_URI': 'stupid://does.not.work:666/goodbye'})
  assert beam
  with beam.app_context():
    with pytest.raises(app.exceptions.UnsupportedDatabase) as e:
      init_db()
  assert e.value.scheme == 'stupid'
  assert str(e.value) == "Unsupported database type/scheme: stupid"
