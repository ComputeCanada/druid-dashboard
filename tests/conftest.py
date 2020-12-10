# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
import pytest

@pytest.fixture(scope='class')
def client(seeded_app):
  return seeded_app.test_client()


@pytest.fixture(scope='module')
def empty_client(empty_app):
  return empty_app.test_client()


@pytest.fixture
def runner(app):
  return app.test_cli_runner()
