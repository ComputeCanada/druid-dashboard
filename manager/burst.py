# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=W0621
#
import json
from manager.db import get_db
from manager.log import get_log
from manager.exceptions import DatabaseException, BadCall
from manager.component import Component

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
          epoch = ?
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

# TODO: These are not limited to "current" bursts
SQL_GET_ALL = '''
  SELECT  id, cluster, account, pain, firstjob, lastjob, state, summary
  FROM    bursts
  WHERE   epoch = ?
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
  SELECT  id, cluster, account, pain, firstjob, lastjob, state, summary
  FROM    bursts
  WHERE   cluster = ? AND epoch = ? AND state='a'
'''

# ---------------------------------------------------------------------------
#                                                                   helpers
# ---------------------------------------------------------------------------

def _make_burst_array(db_results):
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
      epoch=row['epoch']
    ))
  return bursts

def get_cluster_bursts(cluster):
  db = get_db()

  # get epoch from cluster's detector
  detector = Component(cluster=cluster, service='detector')

  # get current bursts
  res = db.execute(SQL_GET_CLUSTER_BURSTS, (cluster, detector.lastheard)).fetchall()
  if not res:
    return None
  return _make_burst_array(res)

def get_current_bursts():
  db = get_db()
  res = db.execute(SQL_GET_CURRENT_BURSTS).fetchall()
  if not res:
    return None
  return _make_burst_array(res)

def get_bursts(cluster=None):
  if cluster:
    return get_cluster_bursts(cluster)
  return get_current_bursts()

def update_burst_states(updates):
  db = get_db()
  for (id, state) in updates.items():
    res = db.execute(SQL_UPDATE_STATE, (state, id))
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
  """

  def __init__(self, id=None, cluster=None, account=None, pain=None,
      jobrange=None, state=None, summary=None, epoch=None):

    self._id = id
    self._cluster = cluster
    self._account = account
    self._pain = pain
    self._jobrange = jobrange
    self._state = state
    self._summary = summary
    self._epoch = epoch

    # handle instantiation by factory
    # pylint: disable=too-many-boolean-expressions
    if id and cluster and account and jobrange and state and \
        pain is not None and summary is not None and epoch is not None:
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
          db.execute(SQL_UPDATE_EXISTING, (pain, jobrange[1], json.dumps(summary), epoch, self._id))
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

  def serializable(self):
    return {
      key.lstrip('_'): val
      for (key, val) in self.__dict__.items()
    }