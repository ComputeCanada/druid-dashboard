# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
from .db import get_db
from .burst import State
from .event import BurstEvent

# ---------------------------------------------------------------------------
#                                                               SQL queries
# ---------------------------------------------------------------------------

SQL_CREATE = '''
  INSERT INTO actions
              (burst_id, analyst, note, timestamp, old_state, new_state)
  VALUES      (?, ?, ?, ?, ?, ?)
'''

SQL_BY_ID = '''
  SELECT  *
  FROM    actions
  WHERE   id = ?
'''

SQL_BY_BURST = '''
  SELECT  *
  FROM    actions
  WHERE   burst_id = ?
'''

# ---------------------------------------------------------------------------
#                                                                   helpers
# ---------------------------------------------------------------------------

def get_by_burst(burstID):
  res = get_db().execute(SQL_BY_BURST, (burstID,)).fetchall()
  if not res:
    raise Exception('TODO: proper exception (Could not retrieve objects)')

  return [
    Action(r['id'], r['burst_id'], r['analyst'], r['timestamp'], r['note'],
      State(r['old_state']), State(r['new_state']))
    for r in res
  ]

# ---------------------------------------------------------------------------
#                                                                Action class
# ---------------------------------------------------------------------------

class Action(BurstEvent):

  def __init__(self, id=None, burstID=None, analyst=None, timestamp=None,
      text=None, old_state=None, new_state=None):

    # if load by ID
    if id and not burstID:
      res = get_db().execute(SQL_BY_ID, (id,)).fetchone()
      if not res:
        raise Exception('TODO: proper exception (Could not retrieve object)')
      self._text = res['note']
      self._old_state = State(res['old_state'])
      self._new_state = State(res['new_state'])
      super().__init__(id, res['burst_id'], res['analyst'], res['timestamp'])

    else:

      # if id is not defined, create new
      if id is None:
        db = get_db()
        res = db.execute(SQL_CREATE, (burstID, analyst, text, timestamp,
          old_state, new_state))
        if not res:
          raise Exception('TODO: proper exception (Could not create new object)')
        db.commit()

      self._text = text
      self._old_state = old_state
      self._new_state = new_state
      super().__init__(id, burstID, analyst, timestamp)
