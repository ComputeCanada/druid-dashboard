# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=W0621
#
import json
from app.db import get_db
from app.log import get_log
from app.exceptions import DatabaseException

# ---------------------------------------------------------------------------
#                                                               SQL queries
# ---------------------------------------------------------------------------

NOTFN_GET_LAST = '''
  SELECT    *
  FROM      notifications
  ORDER BY  id DESC
  LIMIT     ?
'''

NOTFN_GET_SINCE = '''
  SELECT    *
  FROM      notifications
  WHERE     id > ?
  ORDER BY  id DESC
'''

NOTFN_CREATE_NEW = '''
  INSERT INTO notifications
              (context, recipient, sender, message)
  VALUES      (?, ?, ?, ?)
'''

NOTFN_LOAD_BY_ID = '''
  SELECT    *
  FROM      notifications
  WHERE     id = ?
'''

# ---------------------------------------------------------------------------
#                                                      notification helpers
# ---------------------------------------------------------------------------

def get_latest_notifications(last_id=None):
  """
  Provides the latest notifications.

  Args:
    last_id: ID of last notification received or None to get the latest.

  Returns:
    A (possibly empty) list of notification objects.
  """

  db = get_db()
  if last_id:
    results = db.execute(NOTFN_GET_SINCE, (last_id,)).fetchall()
  else:
    results = db.execute(NOTFN_GET_LAST, (1,)).fetchall()
  if results:

    # create list of notifications
    return [
      Notification(
        rec['id'], rec['context'], rec['recipient'], rec['sender'],
        rec['message'], rec['timestamp']
      )
      for rec in results
    ]

  return []

# ---------------------------------------------------------------------------
#                                                        notification class
# ---------------------------------------------------------------------------

class Notification():
  """
  Represents a single notification.

  Attributes:
    _id: unique identifier.
    _context: the target object this notification is for
    _recipient: the user this notification is for
    _sender: the user whose action prompted the notification
    _data: what this notification is about
    _timestamp: the value describing this notification's position in time
  """

  def __init__(
      self, id=None, context=None, recipient=None, sender=None, data=None,
      timestamp=None
  ):

    get_log().debug(
      "In Notification.__init__() with id=%s, context=%s, recipient=%s,"
      " sender=%s, data=%s, timestamp=%s",
      id, context, recipient, sender, data, timestamp
    )

    self._id = id
    self._context = context
    self._recipient = recipient
    self._sender = sender
    self._data = data
    self._timestamp = timestamp

    # creating or retrieving?
    if not id:
      db = get_db()
      serialized = json.dumps(data)
      try:
        db.execute(NOTFN_CREATE_NEW, (context, recipient, sender, serialized))
        db.commit()
      except Exception as e:
        raise DatabaseException("Could not insert new notification") from e
    else:
      # determine what if anything we need to load from database
      if context and recipient and sender and data and timestamp:
        pass
      else:
        self.load()

  def load(self):
    db = get_db()
    res = db.execute(NOTFN_LOAD_BY_ID, (self._id,)).fetchone()
    if res:
      self._context = res['context']
      self._recipient = res['recipient']
      self._sender = res['sender']
      self._data = json.loads(res['message'])
      self._timestamp = res['timestamp']
    else:
      raise ValueError("Could not load notification object by ID")

  def to_dict(self):
    return {
      key.lstrip('_'): val
      for (key, val) in self.__dict__.items()
    }

  @property
  def data(self):
    return self._data

  @property
  def id(self):
    return self._id

  @property
  def sender(self):
    return self._sender

  @property
  def recipient(self):
    return self._recipient
