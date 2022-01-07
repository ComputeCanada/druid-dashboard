# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=W0621
#
import hmac
import base64
from manager.db import get_db
from manager.log import get_log
from manager.exceptions import DatabaseException, BadCall

# how the digest works:
# sh: echo -n "So this is how the world ends" | openssl dgst -sha256 -hmac "secret" -binary | base64
# py: h = hmac.new(b'secret', digestmod='sha256')
#     h.update(b'So this is how the world ends')
#     base64.b64encode(h.digest())

# ---------------------------------------------------------------------------
#                                                               SQL queries
# ---------------------------------------------------------------------------

APIKEY_GET = '''
  SELECT    secret, component
  FROM      apikeys
  WHERE     access = ? AND state = 'a'
'''

APIKEY_GET_ALL = '''
  SELECT    access, component
  FROM      apikeys
  WHERE     state = 'a'
'''

# presentation version
APIKEY_GET_ALL_PRETTY = '''
  SELECT    access, clus.name AS cluster, comp.name AS component
  FROM      apikeys
  JOIN      components comp ON (component = comp.id)
  JOIN      clusters clus on (comp.cluster = clus.id)
  WHERE     state = 'a'
'''

APIKEY_CREATE_NEW = '''
  INSERT INTO apikeys
              (access, secret, component)
  VALUES      (?, ?, ?)
'''

# TODO: revisit (https://git.computecanada.ca/frak/burst/manager/-/issues/51)
# If API key access names shouldn't be used for whatever reason, this is
# another way of deleting keys, but then that needs to be clarified to the
# user
#APIKEY_DELETE = '''
#  UPDATE apikeys
#  SET    state = 'd'
#  WHERE  access = ?
#'''
APIKEY_DELETE = '''
  DELETE FROM apikeys
  WHERE       access = ?
'''

APIKEY_GET_COMPONENT = '''
  SELECT  component
  FROM    apikeys
  WHERE   access = ? AND state = 'a'
'''

APIKEY_MOST_RECENT_USE = '''
  SELECT    lastused
  FROM      apikeys
  WHERE     component = ? AND lastused IS NOT NULL
  ORDER BY  lastused DESC
  LIMIT     1
'''

APIKEY_UPDATE_LAST_USED = '''
  UPDATE    apikeys
  SET       lastused = ?
  WHERE     access = ?
'''


# ---------------------------------------------------------------------------
#                                                                   helpers
# ---------------------------------------------------------------------------

def get_apikeys(pretty=False):
  """
  Retrieves API keys (access part only).

  Args: None.

  Returns:
    A list of API access keys.
  """
  db = get_db()
  sql = APIKEY_GET_ALL_PRETTY if pretty else APIKEY_GET_ALL
  res = db.execute(sql).fetchall()
  if not res:
    return None
  return [
    {
      k: rec[k]
      for k in rec.keys()
    }
    for rec in res
  ]


def add_apikey(access, secret, component):
  get_log().debug("In add_apikey() with: %s=%s for %s", access, secret, component)
  return ApiKey(access, secret, component)


def delete_apikey(access):
  get_log().debug("In delete_apikey() with %s", access)
  db = get_db()
  db.execute(APIKEY_DELETE, (access,))
  db.commit()


def lookup_component(access):
  get_log().debug("In lookup_component with access=%s", access)
  db = get_db()
  row = db.execute(APIKEY_GET_COMPONENT, (access,)).fetchone()
  return row['component']


def most_recent_use(component):
  get_log().debug("In most_recent_use(%s)", component)
  db = get_db()
  row = db.execute(APIKEY_MOST_RECENT_USE, (component,)).fetchone()
  if row:
    get_log().debug("Last used: %s", row['lastused'])
    return row['lastused']
  return None

# ---------------------------------------------------------------------------
#                                                              apikey class
# ---------------------------------------------------------------------------

class ApiKey():
  """
  Represents a single API keypair.

  Attributes:
    _access: unique identifier
    _secret: the secret key used to sign requests
  """

  def __init__(self, access, secret=None, component=None):

    get_log().debug(
      "In ApiKey.__init__() with access=%s, secret=%s", access, secret
    )

    self._access = access
    self._secret = secret

    # creating or retrieving?
    db = get_db()
    if access and not secret:
      res = db.execute(APIKEY_GET, (access,)).fetchone()
      if res:
        self._secret = res['secret']
        self._component = res['component']
      else:
        raise ValueError(
          "Could not load API key with access key '{}'".format(access)
        )
    else:
      if not component:
        raise BadCall("Must specify component")
      try:
        db.execute(APIKEY_CREATE_NEW, (access, secret, component))
        db.commit()
      except Exception as e:
        raise DatabaseException(
          "Could not execute APIKEY_CREATE_NEW with "
          "access='{}', secret='{}', component='{}'".format(
            access, secret, component
          )
        ) from e

  def verify(self, message, digest):

    # calculate digest
    h = hmac.new(self.secret.encode(), digestmod='sha256')
    h.update(message.encode())

    # do they match?
    verified = base64.b64encode(h.digest()).decode('utf-8') == digest

    return verified

  def update_use(self, lastused):
    db = get_db()
    db.execute(APIKEY_UPDATE_LAST_USED, (lastused, self._access))
    db.commit()
    self._lastused = lastused

  @property
  def component(self):
    return self._component

  @property
  def secret(self):
    return self._secret
