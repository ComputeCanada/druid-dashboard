# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
import os
import re
import pytest
from manager.notifier import Notifier, register_notifier, get_notifiers
from manager.case import registry

@pytest.fixture(scope='class')
def client(seeded_app):
  print("Registry (%s) has %d registered reporters" % (registry, len(registry.reporters)))
  return seeded_app.test_client()


@pytest.fixture(scope='class')
def empty_client(empty_app):
  return empty_app.test_client()


@pytest.fixture
def runner(app):
  return app.test_cli_runner()


# pylint: disable=unused-variable,superfluous-parens
def find_seed_update_scripts(basedir, baseversion):

  # dict of version (datestamp) to file
  versions = {}

  # find files looking like 'data-YYYYMMDD.sql'
  regex = re.compile(r'^data-(\d{8})-post\.sql$')

  # walk tests subdirectory
  testsdir = basedir + '/../tests'
  for root, dirs, files in os.walk(testsdir):
    for file in files:
      m = regex.match(file)
      if m:
        version = m[1]
        if int(version) >= int(baseversion):
          versions[m[1]] = '{}/{}'.format(testsdir, file)

  return (versions if versions else None)

# ---------------------------------------------------------------------------
#                                                          notifier fixture
# ---------------------------------------------------------------------------

class TestNotifier(Notifier):

  # pylint: disable=unused-argument
  def _config(self, config):
    self._notifications = []

  def notify(self, message):
    self._notifications.append(message)

  @property
  def notifications(self):
    return self._notifications

  def clear(self):
    self._notifications = []

register_notifier('test', TestNotifier)

@pytest.fixture(scope='class')
def notifier(seeded_app):
  with seeded_app.app_context():
    # TODO: maybe get_notifiers() should return map of type or name to
    # notifier object
    return get_notifiers()[0]
