# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=W0621,raise-missing-from,import-outside-toplevel
#
import json
from manager.db import get_db, DbEnum
from manager.log import get_log
from manager.exceptions import DatabaseException, BadCall, AppException
from manager.component import Component
from manager.cluster import Cluster

# ---------------------------------------------------------------------------
#                                                                     enums
# ---------------------------------------------------------------------------

# enum of states: values are tuple of indicator used in database and the
# display label
# NOTE: if updating this, ensure schema matches
class State(DbEnum):
  PENDING = 'p'
  ACCEPTED  = 'a'
  REJECTED  = 'r'

# enum of resources
class Resource(DbEnum):
  CPU = 'c'
  GPU = 'g'

# ---------------------------------------------------------------------------
#                                                               SQL queries
# ---------------------------------------------------------------------------

SQL_GET = '''
  SELECT    *
  FROM      bursts
  WHERE     id = ?
'''

SQL_FIND_EXISTING = '''
  SELECT  *
  FROM    bursts
  WHERE   cluster = ?
    AND   account = ?
    AND   resource = ?
    AND   ? <= lastjob
'''

SQL_UPDATE_EXISTING = '''
  UPDATE  bursts
  SET     pain = ?,
          lastjob = ?,
          summary = ?,
          epoch = ?,
          ticks = ?
  WHERE   id = ?
'''

SQL_UPDATE_STATE = '''
  UPDATE  bursts
  SET     state = ?
  WHERE   id = ?
'''

SQL_UPDATE_CLAIMANT = '''
  UPDATE  bursts
  SET     claimant = ?
  WHERE   id = ?
'''

SQL_CREATE = '''
  INSERT INTO bursts
              (cluster, account, resource, pain, firstjob, lastjob, submitters, summary, epoch)
  VALUES      (?, ?, ?, ?, ?, ?, ?, ?, ?)
'''

SQL_ACCEPT = '''
  UPDATE  bursts
  SET     state='a'
  WHERE   id = ?
'''

SQL_REJECT = '''
  UPDATE  bursts
  SET     state='r'
  WHERE   id = ?
'''

SQL_GET_CURRENT_BURSTS = '''
  SELECT  B.*
  FROM    bursts B
  JOIN    (
            SELECT    cluster, MAX(epoch) AS epoch
            FROM      bursts
            GROUP BY  cluster
          ) J
  ON      B.cluster = J.cluster AND B.epoch = J.epoch
'''

SQL_GET_CLUSTER_BURSTS = '''
  SELECT  *
  FROM    bursts
  WHERE   cluster = ? AND epoch = ? AND state='a'
'''

SQL_SET_TICKET = '''
  UPDATE  bursts
  SET     ticket_id = ?, ticket_no = ?
  WHERE   id = ?
'''

# ---------------------------------------------------------------------------
#                                                                   helpers
# ---------------------------------------------------------------------------

def _burst_array(db_results):
  bursts = []
  for row in db_results:
    bursts.append(Burst(
      id=row['id'],
      cluster=row['cluster'],
      account=row['account'],
      resource=Resource(row['resource']),
      pain=row['pain'],
      jobrange=(row['firstjob'], row['lastjob']),
      submitters=row['submitters'].split(),
      state=State(row['state']),
      summary=row['summary'],
      epoch=row['epoch'],
      ticks=row['ticks'],
      claimant=row['claimant'],
      ticket_id=row['ticket_id'],
      ticket_no=row['ticket_no']
    ))
  return bursts

def _bursts_by_cluster_epoch(db_results):
  map = {}
  for row in db_results:
    cluster = row['cluster']
    epoch = row['epoch']
    if (cluster, epoch) not in map:
      map[(cluster, epoch)] = []
    map[(cluster, epoch)].append(Burst(
      id=row['id'],
      cluster=row['cluster'],
      account=row['account'],
      resource=Resource(row['resource']),
      pain=row['pain'],
      jobrange=(row['firstjob'], row['lastjob']),
      submitters=row['submitters'].split(),
      state=State(row['state']),
      summary=row['summary'],
      epoch=row['epoch'],
      ticks=row['ticks'],
      claimant=row['claimant'],
      ticket_id=row['ticket_id'],
      ticket_no=row['ticket_no']
    ))
  return map

def get_cluster_bursts(cluster):
  db = get_db()

  # get cluster's detector
  detector = Component(cluster=cluster, service='detector')

  # get current bursts
  res = db.execute(SQL_GET_CLUSTER_BURSTS, (cluster, detector.lastheard)).fetchall()
  if not res:
    return None
  return _burst_array(res)

def get_current_bursts():
  db = get_db()
  res = db.execute(SQL_GET_CURRENT_BURSTS).fetchall()
  if not res:
    return None
  return _bursts_by_cluster_epoch(res)

def get_bursts(cluster=None):
  if cluster:
    return get_cluster_bursts(cluster)
  return get_current_bursts()

def update_bursts(updates, user):
  """
  Update burst information such as state or claimant.

  Args:
    updates (list of dict): list of dicts where each dict contains a burst ID
      and a new value for state and/or claimant.
  """
  from manager.actions import StateUpdate, ClaimantUpdate
  from manager.note import Note

  get_log().debug("In update_bursts()")
  if not updates:
    get_log().error("update_bursts() called with no updates")
    return

  db = get_db()
  for update in updates:

    # get update parameters
    try:
      id = update['id']
      text = update['note']
    except KeyError as e:
      raise BadCall("Burst update missing required field: {}".format(e))
    timestamp = update.get('timestamp', None)

    # update state if applicable
    if state := update.get('state', None):

      s = State.get(state)

      # update history
      try:
        StateUpdate(burstID=id, analyst=user, text=text, timestamp=timestamp,
          state=s.value)
      except KeyError as e:
        error = "Missing required update parameter: {}".format(e)
        raise BadCall(error)
      except Exception as e:
        get_log().error("Exception in creating state update event log: %s", e)
        raise AppException(str(e))

      # update state
      res = db.execute(SQL_UPDATE_STATE, (s.value, id))
      if not res:
        raise DatabaseException("Could not update state for Burst ID {} to {}".format(id, state))

    # update claimant if applicable
    elif 'claimant' in update:

      # if claimant is empty string, use user instead
      claimant = update['claimant'] or user

      get_log().debug("Updating burst %d with claimant %s", id, claimant)

      # update history
      try:
        ClaimantUpdate(burstID=id, analyst=user, text=text,
          timestamp=timestamp, claimant=claimant)
      except Exception as e:
        get_log().error("Exception in creating claimant update event log: %s", e)
        raise AppException(str(e))

      # update claimant
      res = db.execute(SQL_UPDATE_CLAIMANT, (claimant, id))
      if not res:
        raise DatabaseException("Could not update claimant for Burst ID {} to {}".format(id, claimant))

    # otherwise, since we already have the text, this must be just a note
    else:

      try:
        Note(burstID=id, analyst=user, text=text, timestamp=timestamp)
      except Exception as e:
        get_log().error("Exception in creating note: %s", e)
        raise AppException(str(e))

  db.commit()

def set_ticket(id, ticket_id, ticket_no):
  db = get_db()
  res = db.execute(SQL_SET_TICKET, (ticket_id, ticket_no, id))
  if not res:
    raise DatabaseException("Could not set ticket information for Burst ID {}".format(id))
  db.commit()

# ---------------------------------------------------------------------------
#                                                               burst class
# ---------------------------------------------------------------------------

class Burst():
  """
  Represents a burst candidate.

  Attributes:
    _id: id
    _cluster: cluster ID referencing entry in cluster table
    _account: account name (such as 'def-dleske-ab')
    _resource: resource type (type burst.Resource)
    _pain: pain
    _jobrange: tuple of first and last job IDs in burst
    _submitters: submitters associated with the jobs
    _state: state of burst (type burst.State)
    _summary: summary information about burst and jobs (JSON)
    _epoch: epoch timestamp of last report
    _ticks: number of times reported
    _claimant: analyst following up
    _ticket_id: associated ticket's ID
    _ticket_no: associated ticket's number
  """

  def __init__(self, id=None, cluster=None, account=None,
      resource=Resource.CPU, pain=None, jobrange=None, submitters=None,
      state=State.PENDING, summary=None, epoch=None, ticks=0, claimant=None,
      ticket_id=None, ticket_no=None):

    self._id = id
    self._cluster = cluster
    self._account = account
    self._resource = resource
    self._pain = pain
    self._jobrange = jobrange
    self._submitters = submitters
    self._state = state
    self._summary = summary
    self._epoch = epoch
    self._ticks = ticks
    self._claimant = claimant
    self._ticket_id = ticket_id
    self._ticket_no = ticket_no

    # handle instantiation by factory
    # pylint: disable=too-many-boolean-expressions
    # "pain is not None" etc because they are numbers
    if id and cluster and account and jobrange and summary and \
        pain is not None and epoch is not None:

      return

    # verify initialized correctly
    if not (id or (cluster and account and pain is not None and jobrange)):
      get_log().error(
        "Missing either id (%s) or one or more of cluster (%s), account (%s),"
        " pain (%s) or jobrange (%s)",
        id, cluster, account, pain, jobrange
      )
      raise BadCall("Must specify either ID or all burst parameters")

    # creating or retrieving?
    db = get_db()
    if id:
      # lookup operation
      res = db.execute(SQL_GET, (id,)).fetchone()
      if res:
        self._id = id
        self._cluster = res['cluster']
        self._account = res['account']
        self._resource = Resource(res['resource'])
        self._pain = res['pain']
        self._jobrange = (res['firstjob'], res['lastjob'])
        self._submitters = res['submitters'].split()
        self._state = State(res['state'])
        self._summary = json.loads(res['summary']) if res['summary'] else None
        self._epoch = res['epoch']
        self._ticks = res['ticks']
        self._claimant = res['claimant']
        self._ticket_id = res['ticket_id']
        self._ticket_no = res['ticket_no']
      else:
        raise ValueError(
          "Could not load burst with id '{}'".format(id)
        )
    else:
      # see if there is already a suitable burst--one where the current
      # report's starting job falls within the (first, last) range of the
      # existing record
      get_log().debug("Looking for existing burst")
      res = db.execute(SQL_FIND_EXISTING, (cluster, account, resource, jobrange[0])).fetchone()
      if res:
        # found existing burst
        self._id = res['id']
        self._jobrange = [res['firstjob'], jobrange[1]]
        self._ticks = res['ticks'] + 1
        get_log().debug("Ticks updated from %d to %d", res['ticks'], self._ticks)

        # update burst for shifting definition:
        # As time goes on, the first job reported in a burst may have
        # completed, so we want to retain the first job earlier reported.  The
        # end job may also shift outwards as new jobs are queued, so we update
        # that in the database.  Other burst information, such as pain and
        # info, will similarly shift over time, and we'll update that just so
        # the Analyst gets current information from the Manager.

        trying_to = "update existing burst for {}".format(account)
        get_log().debug("Trying to %s", trying_to)

        # update burst record
        try:
          db.execute(SQL_UPDATE_EXISTING, (pain, jobrange[1], json.dumps(summary), epoch, self._ticks, self._id))
        except Exception as e:
          raise DatabaseException("Could not {} ({})".format(trying_to, e)) from e
      else:
        # this is a new burst
        trying_to = "create burst for {}".format(account)
        get_log().debug("Trying to %s", trying_to)

        # create burst record
        try:
          print("Creating new record with submitters: {}".format(submitters))
          db.execute(SQL_CREATE, (
            cluster, account, resource, pain, jobrange[0], jobrange[1], ' '.join(submitters),
            json.dumps(summary), epoch
            )
          )
        except Exception as e:
          raise DatabaseException("Could not {} ({})".format(trying_to, e)) from e
      try:
        db.commit()
      except Exception as e:
        raise DatabaseException("Could not {}".format(trying_to)) from e

  @property
  def ticks(self):
    return self._ticks

  @property
  def state(self):
    return self._state

  @property
  def resource(self):
    return self._resource

  @property
  def ticket_id(self):
    return self._ticket_id

  @property
  def ticket_no(self):
    return self._ticket_no

  @property
  def claimant(self):
    return self._claimant

  @property
  def info(self):
    basic = {
      'account': self._account,
      'cluster': Cluster(self._cluster).name,
      'resource': self._resource,
      'pain': self._pain,
      'submitters': ', '.join(self._submitters)
    }
    if self._summary:
      return dict(basic, **self._summary)
    return basic

  def serialize(self):
    return {
      key.lstrip('_'): val
      for (key, val) in self.__dict__.items()
    }
