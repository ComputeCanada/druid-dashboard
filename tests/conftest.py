# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
import os
import re
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


# pylint: disable=unused-variable,superfluous-parens
def find_seed_update_scripts(basedir):

  # dict of version (datestamp) to file
  versions = {}

  # find files looking like 'data-YYYYMMDD.sql'
  regex = re.compile(r'^data-(\d{8})\.sql$')

  # walk tests subdirectory
  testsdir = basedir + '/../tests'
  for root, dirs, files in os.walk(testsdir):
    for file in files:
      m = regex.match(file)
      if m:
        versions[m[1]] = '{}/{}'.format(testsdir, file)

  return (versions if versions else None)
