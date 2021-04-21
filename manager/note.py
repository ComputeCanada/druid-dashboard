# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=raise-missing-from
#
from .db import get_db
from .event import BurstEvent
from .exceptions import DatabaseException

# ---------------------------------------------------------------------------
#                                                               SQL queries
# ---------------------------------------------------------------------------

SQL_CREATE = '''
  INSERT INTO notes
              (burst_id, analyst, note, timestamp)
  VALUES      (?, ?, ?, ?)
'''

SQL_BY_ID = '''
  SELECT  *
  FROM    notes
  WHERE   id = ?
'''

SQL_BY_BURST = '''
  SELECT  *
  FROM    notes
  WHERE   burst_id = ?
'''

# ---------------------------------------------------------------------------
#                                                                   helpers
# ---------------------------------------------------------------------------

def get_by_burst(burstID):
  try:
    res = get_db().execute(SQL_BY_BURST, (burstID,)).fetchall()
  except Exception as e:
    raise DatabaseException(e)

  return [
    Note(r['id'], r['burst_id'], r['analyst'], r['timestamp'], r['note'])
    for r in res
  ]

# ---------------------------------------------------------------------------
#                                                                Note class
# ---------------------------------------------------------------------------

class Note(BurstEvent):

  def __init__(self, id=None, burstID=None, analyst=None, timestamp=None, text=None):

    # if load by ID
    if id and not burstID:
      res = get_db().execute(SQL_BY_ID, (id,)).fetchone()
      if not res:
        raise Exception('TODO: proper exception (Could not retrieve object)')
      self._text = res['note']
      super().__init__(id, res['burst_id'], res['analyst'], res['timestamp'])

    else:

      # if id is not defined, create new
      if id is None:
        db = get_db()
        res = db.execute(SQL_CREATE, (burstID, analyst, text, timestamp))
        if not res:
          raise Exception('TODO: proper exception (Could not create new object)')
        db.commit()

      self._text = text
      super().__init__(id, burstID, analyst, timestamp)
