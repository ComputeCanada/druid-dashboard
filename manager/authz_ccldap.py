# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=raise-missing-from
#
import re
from manager.log import get_log
from manager.ldap import get_ldap
from manager.authz import Authz, NotAuthorized

# ---------------------------------------------------------------------------
#                                                                   HELPERS
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
#                                                               AUTHZ CLASS
#                                                               for CCLDAP
# ---------------------------------------------------------------------------

class CcLdapAuthz(Authz):

  # TODO: this must be configurable
  _entitlement_re = re.compile(r"frak.computecanada.ca/burst/(?P<entitlement>.*)")

  def __init__(self, user, config=None):
    """ Initialize Authorization class.

    Args:
      user: authenticated user identifier
      config: dict describing configuration.
    """

    super().__init__(user, config)

    # get user details from LDAP record
    details = get_ldap().get_person(user, ['eduPersonEntitlement'])
    get_log().debug("LDAP details for %s: %s", user, details)
    if not details:
      raise NotAuthorized("Could not find LDAP record")

    # parse and validate basic details
    try:
      self._details['name'] = details['cn']
      self._details['id'] = details['cci']
      self._details['given'] = details['givenName']
    except KeyError:
      # all of these are required and/or present in a valid user
      # representing a real user, so without them the app is forbidden
      raise NotAuthorized("Invalid user")

    # parse app entitlements
    if 'eduPersonEntitlement' in details:
      for entitlement in details['eduPersonEntitlement']:
        match = self.__class__._entitlement_re.match(entitlement)
        if match:
          self._entitlements.append(match['entitlement'])
