# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=W0621,raise-missing-from,import-outside-toplevel
#
import json
from flask_babel import _
from manager.db import get_db, DbEnum
from manager.log import get_log
from manager.exceptions import DatabaseException, BadCall, AppException, InvalidApiCall
from manager.cluster import Cluster
from manager.reporter import Reporter, registry, just_job_id
from manager.reportable import Reportable

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

SQL_INSERT_NEW = '''
  INSERT INTO bursts
              (id, account, resource, pain, firstjob, lastjob, submitters)
  VALUES      (?, ?, ?, ?, ?, ?, ?)
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
          submitters = ?
  WHERE   cluster = ?
    AND   account = ?
    AND   resource = ?
    AND   ? <= lastjob
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

SQL_GET_BURSTERS = '''
  SELECT    R.cluster, B.account, B.resource, B.pain
  FROM      reportables R
  JOIN      bursts B
  USING     (id)
  WHERE     R.cluster = ?
    AND     B.state = 'a'
    AND     R.epoch = (
              SELECT MAX(epoch)
                FROM reportables
                WHERE cluster = ?
                AND id IN (SELECT id FROM bursts)
            )
'''

SQL_GET_CURRENT_BURSTS = '''
  SELECT    B.*, COUNT(N.id) AS notes
  FROM      bursts B
  JOIN      (
              SELECT    cluster, MAX(epoch) AS epoch
              FROM      bursts
              GROUP BY  cluster
            ) J
  ON        B.cluster = J.cluster AND B.epoch = J.epoch
  LEFT JOIN notes N
  ON        (B.id = N.burst_id)
  GROUP BY  B.id
'''

SQL_GET_CLUSTER_BURSTS = '''
  SELECT    B.*, COUNT(N.id) AS notes
  FROM      bursts B
  LEFT JOIN notes N
  ON        (B.id = N.burst_id)
  WHERE     cluster = ? AND epoch = ? AND state='a'
  GROUP BY  B.id
'''

SQL_SET_TICKET = '''
  UPDATE  bursts
  SET     ticket_id = ?, ticket_no = ?
  WHERE   id = ?
'''

# ---------------------------------------------------------------------------
#                                                                   helpers
# ---------------------------------------------------------------------------

def _summarize_burst_report(bursts):

  # counts
  newbs = 0
  existing = 0
  claimed = 0
  by_state = {
    State.PENDING: 0,
    State.ACCEPTED: 0,
    State.REJECTED: 0
  }

  for burst in bursts:
    if burst.ticks > 0:
      existing += 1
    else:
      newbs += 1

    if burst.claimant:
      claimed += 1

    by_state[State(burst.state)] += 1

  return "{} new record(s) and {} existing.  In total there are {} pending, " \
    "{} accepted, {} rejected.  {} have been claimed.".format(
      newbs, existing, by_state[State.PENDING], by_state[State.ACCEPTED],
      by_state[State.REJECTED], claimed
    )

# def _burst_array(db_results):
#   bursts = []
#   for row in db_results:
#     bursts.append(Burst(
#       id=row['id'],
#       cluster=row['cluster'],
#       account=row['account'],
#       resource=Resource(row['resource']),
#       pain=row['pain'],
#       jobrange=(row['firstjob'], row['lastjob']),
#       submitters=row['submitters'].split(),
#       state=State(row['state']),
#       summary=row['summary'],
#       epoch=row['epoch'],
#       ticks=row['ticks'],
#       claimant=row['claimant'],
#       ticket_id=row['ticket_id'],
#       ticket_no=row['ticket_no'],
#       other=dict({
#         'notes': row['notes']
#       })
#     ))
#   return bursts

# def _bursts_by_cluster_epoch(db_results):
#   map = {}
#   for row in db_results:
#     cluster = row['cluster']
#     epoch = row['epoch']
#     if (cluster, epoch) not in map:
#       map[(cluster, epoch)] = []
#     map[(cluster, epoch)].append(Burst(
#       id=row['id'],
#       cluster=row['cluster'],
#       account=row['account'],
#       resource=Resource(row['resource']),
#       pain=row['pain'],
#       jobrange=(row['firstjob'], row['lastjob']),
#       submitters=row['submitters'].split(),
#       state=State(row['state']),
#       summary=row['summary'],
#       epoch=row['epoch'],
#       ticks=row['ticks'],
#       claimant=row['claimant'],
#       ticket_id=row['ticket_id'],
#       ticket_no=row['ticket_no'],
#       other=dict({
#         'notes': row['notes']
#       })
#     ))
#   return map

# def get_cluster_bursts(cluster):
#   db = get_db()

#   # get cluster's detector
#   detector = Component(cluster=cluster, service='detector')

#   # TODO: THIS BE BROKEN it assumes only the detector only reports one type of thing ! ! ! ! ! ! ! ! !
#   epoch = detector.lastheard

#   # get current bursts
#   res = db.execute(SQL_GET_CLUSTER_BURSTS, (cluster, epoch)).fetchall()
#   if not res:
#     return None, None
#   return epoch, _burst_array(res)

# def get_current_bursts():
#   db = get_db()
#   res = db.execute(SQL_GET_CURRENT_BURSTS).fetchall()
#   if not res:
#     return None
#   return _bursts_by_cluster_epoch(res)

# def get_bursts(cluster=None):
#   if cluster:
#     return get_cluster_bursts(cluster)
#   return get_current_bursts()

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
      if update['claimant'] == '':
        claimant = user
      else:
        claimant = update['claimant']

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

class Burst(Reporter, Reportable):
  """
  Represents a burst candidate.

  Attributes:
    _id: id
    _cluster: cluster ID referencing entry in cluster table
    _account: account name (such as 'def-dleske-ab')
    _resource: resource type (type burst.Resource)
    _pain: pain metric used as initial indicator of burst candidacy
    _jobrange: tuple of first and last job IDs in burst
    _submitters: submitters associated with the jobs
    _state: state of burst (type burst.State)
    # Common Reportables stuff
    _summary: summary information about burst and jobs (JSON)
    _epoch: epoch timestamp of last report
    _ticks: number of times reported
    _claimant: analyst following up
    _ticket_id: associated ticket's ID
    _ticket_no: associated ticket's number
  """

  # class variables
  _table = 'bursts'

  @classmethod
  def _describe(cls):
    return {
      'table': 'bursts',
      'title': _('Burst candidates'),
      'metric': 'pain',
      'cols': [
        { 'datum': 'account',
          'searchable': True,
          'sortable': True,
          'type': 'text',
          'title': _('Account')
        },
        { 'datum': 'usage',
          'searchable': False,
          'sortable': False,
          'type': 'text',
          'title': _('Usage')
        },
        { 'datum': 'pain',
          'searchable': True,
          'sortable': True,
          'type': 'number',
          'title': _('Pain'),
          'help': _('Numerical indicator of hopelessness inherent in certain job contexts')
        },
        { 'datum': 'summary',
          'searchable': True,
          'sortable': False,
          'type': 'text',
          'title': _('Summary')
        }
      ]
    }

  @classmethod
  def report(cls, cluster, epoch, data):
    """
    Report potential job and/or account issues.

    Args:
      cluster: reporting cluster
      epoch: epoch of report (UTC)
      data: list of dicts describing current instances of potential account
            or job pain or other metrics, as appropriate for the type of
            report.

    Returns:
      String describing summary of report.
    """

    # build list of burst objects from report
    bursts = []
    for burst in data:

      # get the submitted data
      try:
        # pull the others
        res_raw = burst['resource']
        account = burst['account']
        pain = burst['pain']
        summary = burst['summary']
        submitters = burst['submitters']

        # strip job array ID component, if present
        firstjob = just_job_id(burst['firstjob'])
        lastjob = just_job_id(burst['lastjob'])

      except KeyError as e:
        # client not following API
        raise InvalidApiCall("Missing required field: {}".format(e))

      # convert from JSON representations
      try:
        resource = Resource.get(res_raw)
      except KeyError as e:
        raise InvalidApiCall("Invalid resource type: {}".format(e))

      # create burst and append to list
      bursts.append(cls(
        cluster=cluster,
        account=account,
        resource=resource,
        pain=pain,
        submitters=submitters,
        jobrange=(firstjob, lastjob),
        summary=summary,
        epoch=epoch
      ))

    # report event
    return _summarize_burst_report(bursts)

  @classmethod
  def view(cls, criteria):
    """
    Return dict describing view of data reported.

    Args:
      criteria: dict of criteria for selecting data for view.  Accepted by the
                Burst class are `cluster` and `view`.

    Returns:
      Dict describing view of data reported, formatted depending on the
      requested view.  For basic cluster view, in the format:
      ```
      epoch: <seconds since epoch>
      results:
        - obj1.attribute1
        - obj1.attribute2
        - ..
        - obj2.attribute1
        - obj2.attribute2
        - ..
      ```
      For "adjustor" view:
      ```
      ```
    """

    # superclass can handle base case (give me info about the cluster)
    if list(criteria.keys()) == ['cluster']:
      return super().__class__.view(criteria)

    # check that criteria make sense
    try:
      cluster = criteria['cluster']
      view = criteria['view']
    except KeyError:
      raise NotImplementedError
    if view != 'adjustor':
      raise NotImplementedError

    # this view is for reporting accounts deemed burstable by analysts
    res = get_db().execute(SQL_GET_BURSTERS, (cluster, cluster)).fetchall()
    if not res:
      return None
    return [
      {
        'account': rec['account'],
        'pain': rec['pain'],
        'resource': Resource(rec['resource'])
      }
      for rec in res
    ]

  def __init__(self, id=None, record=None, cluster=None, epoch=None,
      account=None, resource=Resource.CPU, pain=None, jobrange=None, submitters=None,
      state=State.PENDING, summary=None, other=None):

    if id or record:
      if record:
        # TODO: This is some jankety crap right here
        record['jobrange'] = (record['firstjob'], record['lastjob'])
        del record['firstjob']
        del record['lastjob']
      super().__init__(id=id, record=record)
      self._resource = Resource(self._resource)
      self._state = State(self._state)
      self._summary = json.loads(self._summary) if self._summary else None
    else:
      self._account = account
      self._resource = resource
      self._pain = pain
      self._jobrange = jobrange
      self._submitters = submitters
      self._state = state
      self._other = other
      super().__init__(cluster=cluster, epoch=epoch, summary=summary)

  def update_existing(self):
    affected = get_db().execute(
      SQL_UPDATE_EXISTING, (
        self._pain, self._jobrange[1], self._submitters, self._cluster,
        self._account, self._resource, self._jobrange[0]
      )).rowcount
    if affected > 1:
      # TODO: better exception
      raise BaseException("Wait, what")
    return affected == 1

  def insert_new(self):
    res = get_db().execute(SQL_INSERT_NEW, (
      self._id, self._account, self._resource, self._pain, self._jobrange[0],
      self._jobrange[1], self._submitters
    ))
    if not res:
      raise BaseException("TODO: Unable to create new Burst record")

##  else:
##    # see if there is already a suitable burst--one where the current
##    # report's starting job falls within the (first, last) range of the
##    # existing record
##    get_log().debug("Looking for existing burst")
##    res = db.execute(SQL_FIND_EXISTING, (cluster, account, resource, jobrange[0])).fetchone()
##    if res:
##      # found existing burst
##      self._id = res['id']
##      self._state = res['state']
##      self._claimant = res['claimant']
##      self._ticket_id = res['ticket_id']
##      self._ticket_no = res['ticket_no']

##      # get union of current and past submitters on this candidate
##      self._submitters = set(res['submitters'].split()) | set(submitters)

##      # update as necessary
##      self._jobrange = [res['firstjob'], jobrange[1]]
##      self._ticks = res['ticks'] + 1
##      get_log().debug("Ticks updated from %d to %d", res['ticks'], self._ticks)

##      # update burst for shifting definition:
##      # As time goes on, the first job reported in a burst may have
##      # completed, so we want to retain the first job earlier reported.  The
##      # end job may also shift outwards as new jobs are queued, so we update
##      # that in the database.  Other burst information, such as pain and
##      # info, will similarly shift over time, and we'll update that just so
##      # the Analyst gets current information from the Manager.

##      trying_to = "update existing burst for {}".format(account)
##      get_log().debug("Trying to %s", trying_to)

##      # update burst record
##      try:
##        db.execute(SQL_UPDATE_EXISTING, (
##          pain, jobrange[1], json.dumps(summary), epoch, self._ticks,
##          ' '.join(self._submitters), self._id)
##        )
##      except Exception as e:
##        raise DatabaseException("Could not {} ({})".format(trying_to, e)) from e

##    else:
##      # this is a new burst
##      trying_to = "create burst for {}".format(account)
##      get_log().debug("Trying to %s", trying_to)

##      # create burst record
##      try:
##        db.execute(SQL_CREATE, (
##          cluster, account, resource, pain, jobrange[0], jobrange[1], ' '.join(submitters),
##          json.dumps(summary), epoch
##          )
##        )
##      except Exception as e:
##        raise DatabaseException("Could not {} ({})".format(trying_to, e)) from e
##    try:
##      db.commit()
##    except Exception as e:
##      raise DatabaseException("Could not {}".format(trying_to)) from e

  @property
  def contact(self):
    """
    Return contact information for this potential issue.  This can depend on
    the type of issue: a PI is responsible for use of the account, so the PI
    should be the contact for questions of resource allocation.  For a
    misconfigured job, the submitting user is probably more appropriate.

    Returns: username of contact.
    """
    return self._account

  @property
  def account(self):
    return self._account

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
  def submitters(self):
    return self._submitters

  @property
  def notes(self):
    if self._other and 'notes' in self._other:
      return self._other['notes']
    return None

  @property
  def info(self):
    basic = {
      'account': self._account,
      'cluster': Cluster(self._cluster).name,
      'resource': self._resource,
      'pain': self._pain,
      'submitters': self._submitters
    }
    if self._summary:
      return dict(basic, **self._summary)
    return basic

  def serialize(self, pretty=False):
    if pretty:
      prettified = {
        'resource_pretty': _(str(self._resource)),
        'state_pretty': _(str(self._state))
      }
      return dict(super().serialize(pretty=True), **prettified)
    return super().serialize()

# ---------------------------------------------------------------------------
#                                                      Burst Reporter class
# ---------------------------------------------------------------------------

# class BurstReporter(Reporter):
#   """
#   Class for reporting bursts: a list of accounts and information about their
#   current job contexts which constitute potential burst candidates.

#   Burst reports are reported via the reports API and may occur with other
#   reports of other metrics or appear on their own, so long as the overall
#   message conforms to the API.

#   Format:
#     ```
#     bursts = [
#       {
#         'account':  character string representing CC account name,
#         'resource': type of resource involved in burst (ex. 'cpu', 'gpu'),
#         'pain':     number indicating pain ratio as defined by Detector,
#         'firstjob': first job owned by account currently in the system,
#         'lastjob':  last job owned by account currently in the system,
#         'submitters': array of user IDs of those submitting jobs,
#         'summary':  JSON-encoded key-value information about burst context
#                     which may be of use to analyst in evaluation
#       },
#       ...
#     ]
#     ```

#   The `jobrange` is used by the Manager and Scheduler to provide a way by
#   which the Scheduler can decide to "unbless" an account--no longer promote it
#   or its jobs to the Burst Pool--without the Detector or the Scheduler needing
#   to maintain independent state.

#   When the Detector signals a potential burst, it reports the first and last
#   jobs (lowest- and highest-numbered) in every report.  The Manager compares
#   this to existing burst candidates.  If the new report overlaps with an
#   existing one, the Manager updates its current understanding with the new upper
#   range.  (The lower range is not updated as this probably only reflects that
#   earlier jobs have been completed, although in the case of mass job deletion
#   this would be misleading, but this range is not intended to be used for any
#   analyst decisions.)

#   The Detector may report several times a day and so will report the same
#   burst candidates multiple times.

#   The Scheduler retrieves affirmed Burst candidates from the Manager.  When
#   a new candidate is pulled, the Scheduler promotes the account to the burst
#   pool.  That account will be provided on every query by the Scheduler, with
#   the job range updated as necessary based on information received by the
#   Manager from the Detector.  Even once the Detector no longer reports this
#   account as a burst candidate, the Manager will maintain its record.

#   The Scheduler will compare the burst record against jobs currently in the
#   system.  If no jobs exist owned by the account that fall within the burst
#   range, then the burst must be complete.  The Scheduler must then report the
#   burst as such to the Manager.
#   """


registry.register('bursts', Burst)
