# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=W0231
#

class AppException(Exception):

  def __init__(self, description):
    self._description = description
    super().__init__()

  def __str__(self):
    return self._description


class BadCall(AppException):
  """
  Exception raised when method called in an unsuitable way, such as a
  nonsensical combination of parameters.
  """

class ResourceNotFound(AppException):
  """
  Exception raised for when requested resources are not available.
  """

class UnsupportedDatabase(AppException):
  """
  Exception raised when application attempts to use unsupported database
  backend.

  Attributes:
    scheme: scheme attempted
  """

  def __init__(self, scheme):
    self._scheme = scheme
    description = "Unsupported database type/scheme: {}".format(scheme)
    super().__init__(description)

  @property
  def scheme(self):
    return self._scheme

class DatabaseException(AppException):
  """
  Exception raised when some database exception occurs.
  """

class UnupgradableDatabase(AppException):
  """
  Exception raised when the database schema expected by the code does not
  match the schema version present in the database.

  Attributes:
    expected: schema version expected by code
    actual: schema version present in database
    available: list of upgrades available that provide a partial upgrade path
  """

  def __init__(self, expected, actual, available):
    self._expected = expected
    self._actual = actual
    self._available = available
    description = \
      'There is no upgrade path available from schema version {} (in the ' \
      'database) to {} (expected by the application).  Available upgrades: '\
      '{}'.format(actual, expected, available)
    super().__init__(description)

class LdapException(AppException):
  """
  Exception raised when some LDAP issue occurs.
  """
