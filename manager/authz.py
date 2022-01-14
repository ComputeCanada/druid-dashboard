# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#

# ---------------------------------------------------------------------------
#                                                                   HELPERS
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
#                                                               exceptions
# ---------------------------------------------------------------------------

class NotAuthorized(Exception):
  # TODO: don't pass
  pass

# ---------------------------------------------------------------------------
#                                                               AUTHZ CLASS
# ---------------------------------------------------------------------------

class Authz:

  def __init__(self, user, config=None):
    """ Initialize Authorization class.

    Args:
      user: authenticated user identifier
      config: dict describing configuration.  Contents of this dict are
        defined by the specialization (subclass) of this class.
    """
    self._user = user
    self._config = config

    # dictionaries for all details about authorization
    self._details = {}
    self._entitlements = []

  @property
  def name(self):
    return self._details['name']

  @property
  def given(self):
    return self._details['given']

  @property
  def id(self):
    return self._details['id']

  @property
  def entitlements(self):
    """ Authorization entitlements.

    Entitlements are authorization labels associated with an identity.  They
    can indicate roles or privileges or other abstracts.
    """
    return self._entitlements or None
