# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=W0621,raise-missing-from,import-outside-toplevel
#
import json
from flask_babel import _
from manager.db import get_db, DbEnum
from manager.exceptions import InvalidApiCall
from manager.reportable import Reportable
from manager.reporter import Reporter, registry

# enum of resources
class JobResource(DbEnum):
  CPU = 'c'
  GPU = 'g'

# ---------------------------------------------------------------------------
#                                                                   helpers
# ---------------------------------------------------------------------------

def json_to_table(str):
  html = ''
  d = json.loads(str)
  if d:
    html += '<table>'
    for k, v in d.items():
      html += f"<tr><th>{k}</th><td>{v}</td></tr>"
    html += '</table>'
  return html

def _summarize_job_age_report(records):
  return f"There are {len(records)} records."

# ---------------------------------------------------------------------------
#                                                               SQL queries
# ---------------------------------------------------------------------------

SQL_FIND_EXISTING = '''
  SELECT    id
  FROM      job_ages
  WHERE     account = ? AND submitter = ? AND resource = ? AND age <= ?
'''

# TODO: if a report comes in for this account, submitter and resource with
# age greater than what's already in the database, it will look like the same
# stuff.  Need to use a job range, or something else.  Using the oldest job
# isn't good enough--the user might try deleting the oldest few or something.
# So maybe job range but unlike with bursts, the job range is NOT updated.
SQL_UPDATE_EXISTING = '''
  UPDATE    job_ages
  SET       age = ?
  WHERE     cluster = ? AND account = ? AND submitter = ? AND resource = ? AND age <= ?
'''

# ---------------------------------------------------------------------------
#                                                             Job Age class
# ---------------------------------------------------------------------------

class JobAge(Reporter, Reportable):

  _table = 'job_ages'

  @classmethod
  def _describe(cls):
    return {
      'table': 'age',
      'title': _('Job age'),
      'metric': 'age',
      'cols': [
        { 'datum': 'account',
          'searchable': True,
          'sortable': True,
          'type': 'text',
          'title': _('Account')
        },
        { 'datum': 'resource',
          'searchable': True,
          'sortable': True,
          'type': 'text',
          'title': _('Resource')
        },
        { 'datum': 'submitter',
          'searchable': True,
          'sortable': True,
          'type': 'text',
          'title': _('User')
        },
        { 'datum': 'age',
          'searchable': True,
          'sortable': True,
          'type': 'number',
          'title': _('Age'),
          'help': _('Days waiting in system')
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

    # build list of objects from report
    records = []
    for record in data:

      # get the submitted data
      try:
        # pull the others
        res_raw = record['resource']
        account = record['account']
        age = record['age']
        summary = record['summary']
        submitter = record['submitter']

      except KeyError as e:
        # client not following API
        raise InvalidApiCall("Missing required field: {}".format(e))

      # convert from JSON representations
      try:
        resource = JobResource.get(res_raw)
      except KeyError as e:
        raise InvalidApiCall("Invalid resource type: {}".format(e))

      records.append(cls(
        cluster=cluster,
        epoch=epoch,
        account=account,
        submitter=submitter,
        resource=resource,
        age=age,
        summary=summary))

    # report event
    return _summarize_job_age_report(records)

  def __init__(self, id=None, record=None, cluster=None, epoch=None,
      account=None, submitter=None, resource=None, age=None, summary=None
  ):
    if id or record:
      super().__init__(id=id, record=record)
    else:
      self._account = account
      self._submitter = submitter
      self._resource = resource
      self._age = age
      self._summary = json.dumps(summary)
      super().__init__(cluster=cluster, epoch=epoch)

  def find_existing(self):
    res = get_db().execute(
      SQL_FIND_EXISTING, (
        self._cluster, self._account, self._submitter,
        self._resource, self._age
      )).fetchone()
    return res.get('id', None)

  def update_existing(self):
    affected = get_db().execute(
      SQL_UPDATE_EXISTING, (
        self._age, self._cluster, self._account, self._submitter, self._resource, self._age
      )).rowcount
    if affected > 1:
      raise BaseException("Wait, what")
    return affected == 1

  @property
  def resource(self):
    return self._resource

  @property
  def summary(self):
    return json.loads(self._summary)

  @property
  def contact(self):
    return self._submitter

  def serialize(self, pretty=False):
    if pretty:
      prettified = {
        'summary_pretty': json_to_table(self._summary),
        'resource_pretty': str(self._resource)
      }
      return dict(super().serialize(pretty=True), **prettified)
    return super().serialize()

# ---------------------------------------------------------------------------
#                                                    Job Age Reporter class
# ---------------------------------------------------------------------------

#class JobAgeReporter(Reporter):
#  """
#  Class for reporting job age: a list of accounts and information about their
#  current jobs with excessive wait times.
#
#  Format:
#    ```
#    job_age = [
#      {
#        'account':  character string representing CC account name,
#        'submitter': username of submitter,
#        'resource': type of resource involved in record (ex. 'cpu', 'gpu'),
#        'age':      number of hours waiting in system, maximal over job
#                    ranges
#        'summary':  JSON-encoded key-value information about record context
#                    which may be of use to analyst in evaluation
#      },
#      ...
#    ]
#    ```
#  """


registry.register('job_age', JobAge)
