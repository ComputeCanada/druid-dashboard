# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=raise-missing-from
#
from .db import get_db
from .event import CaseEvent
from .exceptions import DatabaseException

# ---------------------------------------------------------------------------
#                                                               SQL queries
# ---------------------------------------------------------------------------

SQL_CREATE_HISTORY = '''
  INSERT INTO history
              (case_id, analyst, note, datum, was, now)
  VALUES      (?, ?, ?, ?, ?, ?)
'''

SQL_CREATE_HISTORY_WITH_TIMESTAMP = '''
  INSERT INTO history
              (case_id, analyst, note, timestamp, datum, was, now)
  VALUES      (?, ?, ?, ?, ?, ?, ?)
'''

SQL_GET_HISTORY_BY_ID = '''
  SELECT  *
  FROM    history
  WHERE   id = ?
'''

SQL_GET_HISTORY_BY_CASE = '''
  SELECT    *
  FROM      history
  WHERE     case_id = ?
  ORDER BY  timestamp
'''

# ---------------------------------------------------------------------------
#                                                              History class
# ---------------------------------------------------------------------------

class History(CaseEvent):

  @classmethod
  def get_events(cls, caseID):
    res = get_db().execute(SQL_GET_HISTORY_BY_CASE, (caseID,)).fetchall()
    return [
      History(id=rec['id'], caseID=caseID,
        analyst=rec['analyst'],
        timestamp=rec['timestamp'],
        text=rec['note'],
        datum=rec['datum'],
        was=rec['was'],
        now=rec['now'])
      for rec in res
    ]

  def __init__(self, id=None, caseID=None, analyst=None, timestamp=None,
    text=None, datum=None, was=None, now=None):

    db = get_db()

    # if load by ID
    if id and not caseID:
      res = db.execute(SQL_GET_HISTORY_BY_ID, (id,)).fetchone()
      if not res:
        raise DatabaseException('Could not retrieve record from history with ID {}'.format(id))
      self._text = res['note']
      self._datum = res['datum']
      self._was = res['was']
      self._now = res['now']
      super().__init__(id, res['case_id'], res['analyst'], res['timestamp'])

    else:

      # if id is not defined, create new
      if id is None:
        if timestamp:
          id = db.insert_returning_id(SQL_CREATE_HISTORY_WITH_TIMESTAMP, (
            caseID, analyst, text, timestamp, datum, was, now))
        else:
          id = db.insert_returning_id(SQL_CREATE_HISTORY, (caseID, analyst, text,
            datum, was, now))
        if not id:
          raise DatabaseException('Could not create new record in history')
        db.commit()

      self._text = text
      self._datum = datum
      self._was = was
      self._now = now
      super().__init__(id, caseID, analyst, timestamp)
