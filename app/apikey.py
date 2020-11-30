# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=W0621
#
import hmac
import base64
from app.db import get_db
from app.log import get_log
from app.exceptions import DatabaseException

# ---------------------------------------------------------------------------
#                                                               SQL queries
# ---------------------------------------------------------------------------

APIKEY_GET = '''
  SELECT    secret
  FROM      apikeys
  WHERE     access = ?
'''

APIKEY_GET_ALL = '''
  SELECT    access
  FROM      apikeys
'''

APIKEY_CREATE_NEW = '''
  INSERT INTO apikeys
              (access, secret)
  VALUES      (?, ?)
'''

APIKEY_DELETE = '''
  DELETE FROM apikeys
  WHERE       access = ?
'''

# ---------------------------------------------------------------------------
#                                                                   helpers
# ---------------------------------------------------------------------------

# how the digest works:
# sh: echo -n "So this is how the world ends" | openssl dgst -sha256 -hmac "secret" -binary | base64
# py: h = hmac.new(b'secret', digestmod='sha256')
#     h.update(b'So this is how the world ends')
#     base64.b64encode(h.digest())
def verify_message(access_key, message, digest):

  # get API key
  apikey = ApiKey(access_key)

  # calculate digest
  h = hmac.new(apikey.secret.encode(), digestmod='sha256')
  h.update(message.encode())

  return base64.b64encode(h.digest()).decode('utf-8') == digest

def get_apikeys():
  """
  Retrieves API keys (access part only).

  Args: None.

  Returns:
    A list of API access keys.
  """
  db = get_db()
  res = db.execute(APIKEY_GET_ALL).fetchall()
  if not res:
    return None
  return [row['access'] for row in res]


def add_apikey(access, secret):
  get_log().debug("In add_apikey() with: %s=%s", access, secret)
  return ApiKey(access, secret)

def delete_apikey(access):
  get_log().debug("In delete_apikey() with %s", access)
  db = get_db()
  db.execute(APIKEY_DELETE, (access,))
  db.commit()

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

  def __init__(self, access, secret=None):

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
      else:
        raise ValueError(
          "Could not load API key with access key '{}'".format(access)
        )
    else:
      try:
        db.execute(APIKEY_CREATE_NEW, (access, secret))
        db.commit()
      except Exception as e:
        raise DatabaseException(
          "Could not execute APIKEY_CREATE_NEW with access='{}', secret='{}'".format(access, secret)
        ) from e

  @property
  def secret(self):
    return self._secret
