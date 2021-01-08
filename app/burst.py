# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=W0621
#
from datetime import date
import json
from app.db import get_db
from app.log import get_log
from app.exceptions import DatabaseException, BadCall
from app.apikey import most_recent_use

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
    AND   ? < lastjob
'''

SQL_UPDATE_EXISTING = '''
  UPDATE  bursts
  SET     pain = ?,
          lastjob = ?,
          summary = ?
  WHERE   id = ?
'''

SQL_GET_ALL = '''
  SELECT  id, name, cluster, service
  FROM    bursts
'''

SQL_CREATE = '''
  INSERT INTO bursts
              (cluster, account, pain, firstjob, lastjob, summary)
  VALUES      (?, ?, ?, ?, ?, ?)
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

# ---------------------------------------------------------------------------
#                                                                   helpers
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
#                                                           component class
# ---------------------------------------------------------------------------

class Burst():
  """
  Represents a burst candidate.

  Attributes:
    _id: id
    _account: account: accounting ID (i.e., RAPI)
    _pain: pain
    _jobrange: tuple of first and last job IDs in burst
    _summary: summary information about burst and jobs (dict)
  """

  def __init__(self, id=None, cluster=None, account=None, pain=None, jobrange=None, summary=None):

    self._id = id
    self._account = account
    self._pain = pain
    self._jobrange = jobrange
    self._summary = summary

    ## handle instantiation by factory
    #if factory_load:
    #  if get_last_heard:
    #    self.load_lastheard()
    #  return

    # verify initialized correctly
    if not (id or (cluster and account and pain is not None and jobrange)):
      get_log().error("Missing either id (%s) or one or more of cluster (%s), account (%s), pain (%s) or jobrange (%s)", id, cluster, account, pain, jobrange)
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
      # see if there is already a suitable burst
      res = db.execute(SQL_FIND_EXISTING, (cluster, account, jobrange[1])).fetchone()
      if res:
        # found existing burst
        self._id = res['id']
        self._jobrange[0] = res['firstjob']

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
          db.execute(SQL_UPDATE_EXISTING, (pain, jobrange[1], json.dumps(summary), self._id))
        except Exception as e:
          raise DatabaseException("Could not {} ({})".format(trying_to, e))
      else:
        # this is a new burst
        trying_to = "create burst for {}".format(account)
        get_log().debug("Trying to %s", trying_to)

        # create burst record
        try:
          db.execute(SQL_CREATE, (cluster, account, pain, jobrange[0], jobrange[1], json.dumps(summary)))
        except Exception as e:
          raise DatabaseException("Could not {} ({})".format(trying_to, e))
      try:
        db.commit()
      except Exception as e:
        raise DatabaseException("Could not {}".format(trying_to)) from e

  def serializable(self):
    return {
      key.lstrip('_'): val
      for (key, val) in self.__dict__.items()
    }
