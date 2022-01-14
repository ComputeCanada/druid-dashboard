# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=W0621,raise-missing-from,import-outside-toplevel
#
from flask import current_app
from flask_babel import _
from manager.db import get_db, DbEnum
from manager.log import get_log
from manager.exceptions import InvalidApiCall, DatabaseException
from manager.case import Case, registry, just_job_id

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
              (id, resource, pain, firstjob, lastjob, submitters)
  VALUES      (?, ?, ?, ?, ?, ?)
'''

SQL_UPDATE_BY_ID = '''
  UPDATE    bursts
  SET       pain = ?,
            lastjob = ?,
            submitters = ?
  WHERE     id = ?
'''

SQL_GET_BURSTERS = '''
  SELECT    R.cluster, R.account, B.resource, B.pain
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

# ---------------------------------------------------------------------------
#                                                                   helpers
# ---------------------------------------------------------------------------

def make_graphs_links(cluster, account, resource):
  graphs_base = current_app.config['BURSTS_USAGE_URI']
  graphs_uri = graphs_base.format(cluster=cluster, account=account, resource=resource)
  return f"<a target='beamplot' href='{graphs_uri}'>{_('Dash.cc')}</a>"

# ---------------------------------------------------------------------------
#                                                               burst class
# ---------------------------------------------------------------------------

class Burst(Case):
  """
  Represents a burst candidate.

  Attributes:
    _id: id
    _resource: resource type (type burst.Resource)
    _pain: pain metric used as initial indicator of burst candidacy
    _jobrange: tuple of first and last job IDs in burst
    _submitters: submitters associated with the jobs
    _state: state of burst (type burst.State)
    # Common Reportables stuff
    _cluster: cluster ID referencing entry in cluster table
    _account: account name (such as 'def-dleske-ab')
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
  def describe_me(cls):
    return {
      'title': _('Burst candidates'),
      'metric': 'pain',
      'cols': [
        { 'datum': 'pain',
          'searchable': True,
          'sortable': True,
          'type': 'number',
          'title': _('Pain'),
          'help': _('Numerical indicator of hopelessness inherent in certain job contexts')
        },
        { 'datum': 'resource',
          'searchable': True,
          'sortable': True,
          'type': 'text',
          'title': _('Resource'),
          'help': _('Type of resource (CPU or GPU)')
        },
        { 'datum': 'usage',
          'searchable': False,
          'sortable': False,
          'type': 'text',
          'title': _('Usage')
        },
        { 'datum': 'state',
          'searchable': True,
          'sortable': True,
          'type': 'text',
          'title': _('State')
        }
      ]
    }

  @staticmethod
  def prettify_summary(original):
    field_prettification = {
      'num_jobs': _('Job count'),
      'old_pain': _('Old pain')
     }
    value_prettification = {
      'num_jobs': '%d',
      'old_pain': '%.2f'
    }
    return {
      field_prettification.get(x, x): value_prettification.get(x, '%s') % (y)
      for x, y in original.items()
    }

  @classmethod
  def summarize_report(cls, cases):

    # counts
    newbs = 0
    existing = 0
    claimed = 0
    by_state = {
      State.PENDING: 0,
      State.ACCEPTED: 0,
      State.REJECTED: 0
    }

    for burst in cases:
      if burst.ticks > 1:
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
        jobrange=[firstjob, lastjob],
        summary=summary,
        epoch=epoch
      ))

    # report event
    return cls.summarize_report(bursts)

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
    # if nothing other than pretty and cluster are in keys, we're good
    # cluster is required, pretty may be included
    if set(criteria.keys()) - {'pretty'} == {'cluster'}:
      return super(Burst, cls).view(criteria)

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

      # initialize through base class and then make own interpretations
      super().__init__(id=id, record=record)
      self._resource = Resource(self._resource)
      self._state = State(self._state)
      self._submitters = self._submitters.split()

      # fix base class's interpretation
      self._jobrange = [self._firstjob, self._lastjob]
      del self.__dict__['_firstjob']
      del self.__dict__['_lastjob']

    else:

      self._resource = resource
      self._pain = pain
      self._jobrange = jobrange
      self._submitters = submitters
      self._state = state
      self._other = other
      super().__init__(account=account, cluster=cluster, epoch=epoch, summary=summary)

  def find_existing_query(self):
    return (
      "resource = ? AND ? <= lastjob",
      (self._resource, self._jobrange[0]),
      ['resource', 'pain', 'submitters', 'state', 'firstjob', 'lastjob']
    )

  def update_existing_me(self, rec):
    self._state = rec['state']
    self._jobrange[0] = rec['firstjob']

    # update list of submitters, prioritizing new submitters
    self._submitters = self._submitters + [ x for x in rec['submitters'].split() if x not in self._submitters ]

    affected = get_db().execute(SQL_UPDATE_BY_ID, (
      self._pain, self._jobrange[1], ' '.join(self._submitters), self._id
    )).rowcount

    return affected == 1

  def insert_new(self):
    res = get_db().execute(SQL_INSERT_NEW, (
      self._id, self._resource, self._pain, self._jobrange[0],
      self._jobrange[1], ' '.join(self._submitters)
    ))
    if not res:
      errmsg = "Unable to create new Burst record"
      get_log().error(errmsg)
      raise DatabaseException(errmsg)

  def update(self, update, who):
    if update.get('datum', None) == 'state':
      update['value'] = State.get(update['value'])
    super().update(update, who)

  @property
  def state(self):
    return self._state

  @property
  def resource(self):
    return self._resource

  @property
  def users(self):
    return self._submitters

  @property
  def info(self):
    d = super().info
    d['pain'] = self._pain
    d['resource'] = str(self._resource)
    return d

  def serialize(self, pretty=False):
    # have superclass start serialization but we'll handle the summary
    serialized = super().serialize(pretty)

    if pretty:
      serialized['resource_pretty'] = _(str(self._resource))
      serialized['state_pretty'] = _(str(self._state))
      serialized['pain_pretty'] = "%.2f" % (self._pain)
      serialized['usage_pretty'] = make_graphs_links(
        self._cluster, self._account, str(self._resource).lower())

      # determine actions
      if self._state == State.PENDING:
        serialized['actions'] = [{
          'id': 'reject',
          'label': _('Reject')
        }]
        if self._ticket_id:
          serialized['actions'].append({
            'id': 'accept',
            'label': _('Accept')
          })

    return serialized

# register class with reporter registry
registry.register('bursts', Burst)
