# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=raise-missing-from
#
import json
from .db import get_db
from .event import CaseEvent
from .exceptions import ResourceNotFound, ResourceNotCreated

# ---------------------------------------------------------------------------
#                                                               SQL queries
# ---------------------------------------------------------------------------

SQL_CREATE_HISTORY = '''
  INSERT INTO history
              (case_id, analyst, note, change)
  VALUES      (?, ?, ?, ?)
'''

SQL_CREATE_HISTORY_WITH_TIMESTAMP = '''
  INSERT INTO history
              (case_id, analyst, note, timestamp, change)
  VALUES      (?, ?, ?, ?, ?)
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
  def _make_dict(cls, datum, was, now):
    if datum is None:
      return None
    return {
      'datum': datum,
      'was': was,
      'now': now
    }

  @classmethod
  def get_events(cls, caseID):
    res = get_db().execute(SQL_GET_HISTORY_BY_CASE, (caseID,)).fetchall()
    if not res:
      return None
    return [ History(record=rec) for rec in res ]

  def __init__(self, id=None, caseID=None, record=None, analyst=None, timestamp=None,
    text=None, datum=None, was=None, now=None):

    db = get_db()

    # if load by ID
    if id and not record:
      res = db.execute(SQL_GET_HISTORY_BY_ID, (id,)).fetchone()
      if not res:
        raise ResourceNotFound('Could not retrieve record from history with ID {}'.format(id))
      self._text = res['note']
      self._change = json.loads(res['change'])
      super().__init__(id, res['case_id'], res['analyst'], res['timestamp'])

    elif record:

      self._text = record['note']
      self._change = json.loads(record['change'])
      super().__init__(record['id'], record['case_id'], record['analyst'], record['timestamp'])

    else:

      self._text = text
      self._change = self._make_dict(datum, was, now)

      # if id is not defined, create new
      if id is None:
        if timestamp:
          id = db.insert_returning_id(SQL_CREATE_HISTORY_WITH_TIMESTAMP, (
            caseID, analyst, self._text, timestamp, json.dumps(self._change)
          ))
        else:
          id = db.insert_returning_id(SQL_CREATE_HISTORY, (
            caseID, analyst, self._text, json.dumps(self._change)
          ))
        if not id:
          raise ResourceNotCreated('Could not create new record in history')
        db.commit()

      super().__init__(id, caseID, analyst, timestamp)
