# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=raise-missing-from
#
from .db import get_db
from .burst import State
from .event import BurstEvent
from .exceptions import DatabaseException

# ---------------------------------------------------------------------------
#                                                               SQL queries
# ---------------------------------------------------------------------------

SQL_CREATE_STATE_UPDATE_WITH_TIMESTAMP = '''
  INSERT INTO updates_state
              (burst_id, analyst, note, timestamp, old_state, new_state)
  VALUES      (?, ?, ?, ?, (SELECT state FROM bursts WHERE id=?), ?)
'''

SQL_CREATE_STATE_UPDATE = '''
  INSERT INTO updates_state
              (burst_id, analyst, note, old_state, new_state)
  VALUES      (?, ?, ?, (SELECT state FROM bursts WHERE id=?), ?)
'''

SQL_STATE_UPDATE_BY_ID = '''
  SELECT  *
  FROM    updates_state
  WHERE   id = ?
'''

SQL_STATE_UPDATES_BY_BURST = '''
  SELECT  *
  FROM    updates_state
  WHERE   burst_id = ?
'''

SQL_CREATE_CLAIMANT_UPDATE = '''
  INSERT INTO updates_claimant
              (burst_id, analyst, note, claimant_was, claimant_now)
  VALUES      (?, ?, ?, (SELECT claimant FROM bursts WHERE id=?), ?)
'''

SQL_CREATE_CLAIMANT_UPDATE_WITH_TIMESTAMP = '''
  INSERT INTO updates_claimant
              (burst_id, analyst, note, timestamp, claimant_was, claimant_now)
  VALUES      (?, ?, ?, ?, (SELECT claimant FROM bursts WHERE id=?), ?)
'''

SQL_CLAIMANT_UPDATE_BY_ID = '''
  SELECT  *
  FROM    updates_claimant
  WHERE   id = ?
'''

SQL_CLAIMANT_UPDATES_BY_BURST = '''
  SELECT  *
  FROM    updates_claimant
  WHERE   burst_id = ?
'''

# ---------------------------------------------------------------------------
#                                                                   helpers
# ---------------------------------------------------------------------------

def get_by_burst(burstID):

  state_updates = None
  claimant_updates = None

  try:
    res = get_db().execute(SQL_STATE_UPDATES_BY_BURST, (burstID,)).fetchall()
  except Exception as e:
    raise DatabaseException(e)
  if res:
    state_updates = [
      StateUpdate(r['id'], r['burst_id'], r['analyst'], r['timestamp'], r['note'],
        State(r['new_state']), State(r['old_state']))
      for r in res
    ]

  try:
    res = get_db().execute(SQL_CLAIMANT_UPDATES_BY_BURST, (burstID,)).fetchall()
  except Exception as e:
    raise DatabaseException(e)

  if res:
    claimant_updates = [
      ClaimantUpdate(r['id'], r['burst_id'], r['analyst'], r['timestamp'], r['note'],
        r['claimant_now'], r['claimant_was'])
      for r in res
    ]

  if state_updates and claimant_updates:
    return state_updates + claimant_updates
  elif state_updates:
    return state_updates
  else:
    return claimant_updates

# ---------------------------------------------------------------------------
#                                                         StateUpdate class
# ---------------------------------------------------------------------------

class StateUpdate(BurstEvent):

  def __init__(self, id=None, burstID=None, analyst=None, timestamp=None,
      text=None, state=None, old_state=None):

    # if load by ID
    if id and not burstID:
      res = get_db().execute(SQL_STATE_UPDATE_BY_ID, (id,)).fetchone()
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
        if timestamp:
          res = db.execute(SQL_CREATE_STATE_UPDATE_WITH_TIMESTAMP, (
            burstID, analyst, text, timestamp, burstID, state))
        else:
          res = db.execute(SQL_CREATE_STATE_UPDATE, (
            burstID, analyst, text, burstID, state))
        if not res:
          raise Exception('TODO: proper exception (Could not create new object)')

      self._text = text
      self._old_state = old_state
      self._new_state = state
      super().__init__(id, burstID, analyst, timestamp)

# ---------------------------------------------------------------------------
#                                                      ClaimantUpdate class
# ---------------------------------------------------------------------------

class ClaimantUpdate(BurstEvent):

  def __init__(self, id=None, burstID=None, analyst=None, timestamp=None,
      text=None, claimant=None, claimant_was=None):

    # if load by ID
    if id and not burstID:
      res = get_db().execute(SQL_CLAIMANT_UPDATE_BY_ID, (id,)).fetchone()
      if not res:
        raise Exception('TODO: proper exception (Could not retrieve object)')
      self._text = res['note']
      self._claimant_was = res['claimant_was']
      self._claimant_now = res['claimant_now']
      super().__init__(id, res['burst_id'], res['analyst'], res['timestamp'])

    else:

      # if id is not defined, create new
      if id is None:
        db = get_db()
        if timestamp:
          res = db.execute(SQL_CREATE_CLAIMANT_UPDATE_WITH_TIMESTAMP, (
            burstID, analyst, text, timestamp, burstID, claimant))
        else:
          res = db.execute(SQL_CREATE_CLAIMANT_UPDATE, (burstID, analyst, text,
            burstID, claimant))
        if not res:
          raise Exception('TODO: proper exception (Could not create new object)')

      self._text = text
      self._claimant_was = claimant_was
      self._claimant_now = claimant
      super().__init__(id, burstID, analyst, timestamp)
