# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
_fake_tree = {
  'admin1': {
    'givenName': 'Admin 1',
    'preferredLanguage': 'en',
    'cn': 'Test Admin 1',
    'cci': 'tst-001',
    'eduPersonEntitlement': ['frak.computecanada.ca/burst/admin'],
  },
  'pi1': {
    'givenName': 'PI 1',
    'preferredLanguage': 'en',
    'cn': 'Test PI 1',
    'cci': 'tst-002',
    'ccPrimaryEmail': ['drew.leske+pi1@computecanada.ca']
  },
  'user1': {
    'cn': 'Test User 1',
    'givenName': 'User 1',
    'preferredLanguage': 'en',
    'cci': 'tst-003',
    'ccPrimaryEmail': ['drew.leske+user1@computecanada.ca'],
    'eduPersonEntitlement': ['frak.computecanada.ca/burst/analyst'],
  },
  'user2': {
    'cn': 'Test User 2',
    'givenName': 'User 2',
    'cci': 'tst-004'
  },
  'user3': {
    'cn': 'Test User 3',
    'givenName': 'User 3',
    'preferredLanguage': 'fr',
    'cci': 'tst-006',
    'ccPrimaryEmail': ['drew.leske+user3@computecanada.ca']
  },
  'ldapcanary': {
    'cn': 'Fake Canary',
    'cci': 'tst-005'
  }
}

_projects = {
  'def-pi1': {
    'dn': 'def-pi1,ou=Group,dc=fakey,dc=fake',
    'ccRapi': 'tst-002-aa',
    'description': '',
    'ccResponsible': 'tst-002',
    'members': ['tst-005', 'tst-006']
  },
}

# create CCI-indexed tree
_fake_tree_by_cci = {}
for key, rec in _fake_tree.items():
  rec['uid'] = key
  _fake_tree_by_cci[rec['cci']] = rec

class LdapStub():
  def __init__(self):
    pass

  #pylint: disable=unused-argument,no-self-use
  def get_person(self, uid, additional=None):
    return _fake_tree.get(uid, None)

  #pylint: disable=unused-argument,no-self-use
  def get_person_by_cci(self, cci, additional=None):
    return _fake_tree_by_cci.get(cci, None)

  def get_project(self, cn):
    return _projects.get(cn, None)
