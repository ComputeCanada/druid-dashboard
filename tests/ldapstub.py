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
    'cci': 'tst-002'
  },
  'user2': {
    'cn': 'Test User 2',
    'givenName': 'User 2'
  }
}

class LdapStub():
  def __init__(self):
    pass

  #pylint: disable=unused-argument,no-self-use
  def get_person(self, uid, additional=None):
    return _fake_tree.get(uid, None)
