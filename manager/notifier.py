# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
import json
from manager.db import get_db

# ---------------------------------------------------------------------------
#                                                               SQL queries
# ---------------------------------------------------------------------------

SQL_LIST_NOTIFIERS = """
  SELECT  name, type
  FROM    notifiers
"""

SQL_GET_NOTIFIERS = """
  SELECT  *
  FROM    notifiers
"""

SQL_GET_NOTIFIER = """
  SELECT  *
  FROM    notifiers
  WHERE   name = ?
"""

# ---------------------------------------------------------------------------
#                                                                   helpers
# ---------------------------------------------------------------------------

# this is where notifiers are stored
notifiers = {}
notifiers_inited = None

def register_notifier(type, cls):
  print("In register_notifiers()")
  notifiers[type] = cls

def list_notifiers():
  db = get_db()
  return db.execute(SQL_LIST_NOTIFIERS).fetchall()

def get_notifiers():
  # TODO: why can't I use g.notifiers for this?
  # pylint: disable=global-statement
  global notifiers_inited
  if not notifiers_inited:
    db = get_db()
    res = db.execute(SQL_GET_NOTIFIERS).fetchall()
    if not res:
      return None
    notifiers_inited = [
      notifiers[row['type']](row['name'], json.loads(row['config']))
      for row in res
    ]
  return notifiers_inited

def clear_notifiers():
  for notifier in get_notifiers():
    notifier.clear()

# ---------------------------------------------------------------------------
#                                                            Notifier class
# ---------------------------------------------------------------------------

class Notifier():

  def __init__(self, name, config):

    self._name = name
    self._config(config)

  def _config(self, config):

    raise NotImplementedError

  def clear(self):
    pass

  def notify(self, message):

    raise NotImplementedError

  def _serialize(self):

    return {
      key.lstrip('_'): val
      for (key, val) in self.__dict__.items()
    }

  def _deserialize(self, dict):

    for (key, val) in dict:
      self.__dict__[key] = val
