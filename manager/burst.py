# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=W0621
#
import json
from enum import Enum
from flask_babel import _
from manager.db import get_db
from manager.log import get_log
from manager.exceptions import DatabaseException, BadCall
from manager.component import Component

# ---------------------------------------------------------------------------
#                                                                     enums
# ---------------------------------------------------------------------------

# enum of states: values are tuple of indicator used in database and the
# display label
# NOTE: if updating this, ensure schema matches
class State(Enum):
  UNACTIONED  = 'p'
  CLAIMED     = 'c'
  TICKETED    = 't'
  ACCEPTED    = 'a'
  REJECTED    = 'r'

  def __str__(self):
    return {
      'p': _('Unactioned'),
      'c': _('Claimed'),
      't': _('Ticketed'),
      'a': _('Accepted'),
      'r': _('Rejected')
    }[self.value]

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

SQL_CREATE = '''
  INSERT INTO bursts
              (cluster, account, pain, firstjob, lastjob, summary, epoch)
  VALUES      (?, ?, ?, ?, ?, ?, ?)
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
      pain=row['pain'],
      jobrange=(row['firstjob'], row['lastjob']),
      state=row['state'],
      summary=row['summary'],
      epoch=row['epoch'],
      ticks=row['ticks']
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
      pain=row['pain'],
      jobrange=(row['firstjob'], row['lastjob']),
      state=row['state'],
      summary=row['summary'],
      epoch=row['epoch'],
      ticks=row['ticks']
    ))
  return map

def get_cluster_bursts(cluster):
  db = get_db()

  # get epoch from cluster's detector
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

def update_burst_states(updates):
  db = get_db()
  for (id, state) in updates.items():
    res = db.execute(SQL_UPDATE_STATE, (State(state).value, id))
    # TODO: consider catching from above
    # except ValueError:
    #   raise Exception()
    if not res:
      raise DatabaseException("Could not update state for Burst ID {} to {}".format(id, state))
  db.commit()

# ---------------------------------------------------------------------------
#                                                           component class
# ---------------------------------------------------------------------------

class Burst():
  """
  Represents a burst candidate.

  Attributes:
    _id: id
    _cluster: cluster ID referencing entry in cluster table
    _account: account: accounting ID (i.e., RAPI)
    _pain: pain
    _jobrange: tuple of first and last job IDs in burst
    _state: state of burst
    _summary: summary information about burst and jobs (JSON)
    _epoch: epoch timestamp of last report
    _ticks: number of times reported
  """

  def __init__(self, id=None, cluster=None, account=None, pain=None,
      jobrange=None, state='p', summary=None, epoch=None, ticks=0):

    self._id = id
    self._cluster = cluster
    self._account = account
    self._pain = pain
    self._jobrange = jobrange
    self._state = State(state)
    self._summary = summary
    self._epoch = epoch
    self._ticks = ticks

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
        # TODO: will this case be used?
        pass
      else:
        raise ValueError(
          "Could not load burst with id '{}'".format(id)
        )
    else:
      # see if there is already a suitable burst--one where the current
      # report's starting job falls within the (first, last) range of the
      # existing record
      get_log().debug("Looking for existing burst")
      res = db.execute(SQL_FIND_EXISTING, (cluster, account, jobrange[0])).fetchone()
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
          db.execute(SQL_CREATE, (cluster, account, pain, jobrange[0], jobrange[1], json.dumps(summary), epoch))
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

  def serializable(self):
    return {
      key.lstrip('_'): val.value if issubclass(type(val), Enum) else val
      for (key, val) in self.__dict__.items()
    }
