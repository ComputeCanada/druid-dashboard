# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=raise-missing-from
#
from .db import get_db
from .event import BurstEvent
from .exceptions import DatabaseException

# ---------------------------------------------------------------------------
#                                                               SQL queries
# ---------------------------------------------------------------------------

##SQL_CREATE_STATE_UPDATE_WITH_TIMESTAMP = '''
##  INSERT INTO updates_state
##              (burst_id, analyst, note, timestamp, old_state, new_state)
##  VALUES      (?, ?, ?, ?, (SELECT state FROM bursts WHERE id=?), ?)
##'''

##SQL_CREATE_STATE_UPDATE = '''
##  INSERT INTO updates_state
##              (burst_id, analyst, note, old_state, new_state)
##  VALUES      (?, ?, ?, (SELECT state FROM bursts WHERE id=?), ?)
##'''

##SQL_STATE_UPDATE_BY_ID = '''
##  SELECT  *
##  FROM    updates_state
##  WHERE   id = ?
##'''

##SQL_STATE_UPDATES_BY_BURST = '''
##  SELECT  *
##  FROM    updates_state
##  WHERE   burst_id = ?
##'''

##SQL_CREATE_CLAIMANT_UPDATE = '''
##  INSERT INTO updates_claimant
##              (burst_id, analyst, note, claimant_was, claimant_now)
##  VALUES      (?, ?, ?, (SELECT claimant FROM bursts WHERE id=?), ?)
##'''

##SQL_CREATE_CLAIMANT_UPDATE_WITH_TIMESTAMP = '''
##  INSERT INTO updates_claimant
##              (burst_id, analyst, note, timestamp, claimant_was, claimant_now)
##  VALUES      (?, ?, ?, ?, (SELECT claimant FROM bursts WHERE id=?), ?)
##'''

##SQL_CLAIMANT_UPDATE_BY_ID = '''
##  SELECT  *
##  FROM    updates_claimant
##  WHERE   id = ?
##'''

##SQL_CLAIMANT_UPDATES_BY_BURST = '''
##  SELECT  *
##  FROM    updates_claimant
##  WHERE   burst_id = ?
##'''

SQL_CREATE_UPDATE = '''
  INSERT INTO history
              (case_id, analyst, note, datum, was, now)
  VALUES      (?, ?, ?, ?, ?, ?)
'''

SQL_CREATE_UPDATE_WITH_TIMESTAMP = '''
  INSERT INTO history
              (case_id, analyst, note, timestamp, datum, was, now)
  VALUES      (?, ?, ?, ?, ?, ?, ?)
'''

SQL_GET_UPDATE_BY_ID = '''
  SELECT  *
  FROM    history
  WHERE   id = ?
'''

SQL_GET_UPDATES_BY_REPORTABLE = '''
  SELECT  *
  FROM    history
  WHERE   case_id = ?
'''

### ---------------------------------------------------------------------------
###                                                                   helpers
### ---------------------------------------------------------------------------

##def get_by_burst(burstID):

##  state_updates = None
##  claimant_updates = None

##  try:
##    res = get_db().execute(SQL_STATE_UPDATES_BY_BURST, (burstID,)).fetchall()
##  except Exception as e:
##    raise DatabaseException(e)
##  if res:
##    state_updates = [
##      StateUpdate(r['id'], r['burst_id'], r['analyst'], r['timestamp'], r['note'],
##        State(r['new_state']), State(r['old_state']))
##      for r in res
##    ]

##  try:
##    res = get_db().execute(SQL_CLAIMANT_UPDATES_BY_BURST, (burstID,)).fetchall()
##  except Exception as e:
##    raise DatabaseException(e)

##  if res:
##    claimant_updates = [
##      ClaimantUpdate(r['id'], r['burst_id'], r['analyst'], r['timestamp'], r['note'],
##        r['claimant_now'], r['claimant_was'])
##      for r in res
##    ]

##  if state_updates and claimant_updates:
##    return state_updates + claimant_updates
##  if state_updates:
##    return state_updates
##  return claimant_updates

### ---------------------------------------------------------------------------
###                                                         StateUpdate class
### ---------------------------------------------------------------------------

##class StateUpdate(BurstEvent):

##  def __init__(self, id=None, burstID=None, analyst=None, timestamp=None,
##      text=None, state=None, old_state=None):

##    # if load by ID
##    if id and not burstID:
##      res = get_db().execute(SQL_STATE_UPDATE_BY_ID, (id,)).fetchone()
##      if not res:
##        raise DatabaseException('Could retrieve record from updates_state with ID {}'.format(id))
##      self._text = res['note']
##      self._old_state = State(res['old_state'])
##      self._new_state = State(res['new_state'])
##      super().__init__(id, res['burst_id'], res['analyst'], res['timestamp'])

##    else:

##      # if id is not defined, create new
##      if id is None:
##        db = get_db()
##        if timestamp:
##          res = db.execute(SQL_CREATE_STATE_UPDATE_WITH_TIMESTAMP, (
##            burstID, analyst, text, timestamp, burstID, state))
##        else:
##          res = db.execute(SQL_CREATE_STATE_UPDATE, (
##            burstID, analyst, text, burstID, state))
##        if not res:
##          raise DatabaseException('Could not create new record in updates_state')

##      self._text = text
##      self._old_state = old_state
##      self._new_state = state
##      super().__init__(id, burstID, analyst, timestamp)

### ---------------------------------------------------------------------------
###                                                      ClaimantUpdate class
### ---------------------------------------------------------------------------

##class ClaimantUpdate(BurstEvent):

##  def __init__(self, id=None, burstID=None, analyst=None, timestamp=None,
##      text=None, claimant=None, claimant_was=None):

##    # if load by ID
##    if id and not burstID:
##      res = get_db().execute(SQL_CLAIMANT_UPDATE_BY_ID, (id,)).fetchone()
##      if not res:
##        raise DatabaseException('Could retrieve record from updates_claimant with ID {}'.format(id))
##      self._text = res['note']
##      self._claimant_was = res['claimant_was']
##      self._claimant_now = res['claimant_now']
##      super().__init__(id, res['burst_id'], res['analyst'], res['timestamp'])

##    else:

##      # if id is not defined, create new
##      if id is None:
##        db = get_db()
##        if timestamp:
##          res = db.execute(SQL_CREATE_CLAIMANT_UPDATE_WITH_TIMESTAMP, (
##            burstID, analyst, text, timestamp, burstID, claimant))
##        else:
##          res = db.execute(SQL_CREATE_CLAIMANT_UPDATE, (burstID, analyst, text,
##            burstID, claimant))
##        if not res:
##          raise DatabaseException('Could not create new record in updates_claimant')

##      self._text = text
##      self._claimant_was = claimant_was
##      self._claimant_now = claimant
##      super().__init__(id, burstID, analyst, timestamp)

##    if self._claimant_was:
##      self._claimant_was_pretty = get_ldap().get_person_by_cci(self._claimant_was)['givenName']
##    if self._claimant_now:
##      self._claimant_now_pretty = get_ldap().get_person_by_cci(self._claimant_now)['givenName']

# ---------------------------------------------------------------------------
#                                                              Update class
# ---------------------------------------------------------------------------

class Update(BurstEvent):

  def __init__(self, id=None, caseID=None, analyst=None, timestamp=None,
    text=None, datum=None, was=None, now=None):

    db = get_db()

    # if load by ID
    if id and not caseID:
      res = db.execute(SQL_GET_UPDATE_BY_ID, (id,)).fetchone()
      if not res:
        raise DatabaseException('Could not retrieve record from updates with ID {}'.format(id))
      self._text = res['note']
      self._datum = res['datum']
      self._was = res['was']
      self._now = res['now']
      super().__init__(id, res['case_id'], res['analyst'], res['timestamp'])

    else:

      # if id is not defined, create new
      if id is None:
        if timestamp:
          res = db.execute(SQL_CREATE_UPDATE_WITH_TIMESTAMP, (
            caseID, analyst, text, timestamp, datum, was, now))
        else:
          res = db.execute(SQL_CREATE_UPDATE, (caseID, analyst, text,
            datum, was, now))
        if not res:
          raise DatabaseException('Could not create new record in updates')

      self._text = text
      self._datum = datum
      self._was = was
      self._now = now
      super().__init__(id, caseID, analyst, timestamp)
