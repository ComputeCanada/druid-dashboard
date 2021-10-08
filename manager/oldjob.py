# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=W0621,raise-missing-from,import-outside-toplevel
#
from flask_babel import _
from manager.log import get_log
from manager.db import get_db, DbEnum
from manager.exceptions import InvalidApiCall, ResourceNotCreated
from manager.case import Case, registry

# enum of resources
class JobResource(DbEnum):
  CPU = 'c'
  GPU = 'g'

# ---------------------------------------------------------------------------
#                                                               SQL queries
# ---------------------------------------------------------------------------

SQL_INSERT_NEW = '''
  INSERT INTO oldjobs
              (id, submitter, resource, age)
  VALUES      (?, ?, ?, ?)
'''

SQL_UPDATE_BY_ID = '''
  UPDATE  oldjobs
  SET     age = ?, submitter = ?
  WHERE   id = ?
'''

# ---------------------------------------------------------------------------
#                                                             Old Job class
# ---------------------------------------------------------------------------

class OldJob(Case):

  _table = 'oldjobs'

  @classmethod
  def describe_me(cls):
    return {
      'title': _('Job age'),
      'metric': 'age',
      'cols': [
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

    Format:
    ```
    data = [
      {
        'account':  character string representing CC account name,
        'resource': type of resource involved in record (ex. 'cpu', 'gpu'),
        'age':      number of hours waiting in system, maximal over job
                    ranges
        'submitter': username of submitter,
        'summary':  JSON-encoded key-value information about record context
                    which may be of use to analyst in evaluation
      },
      ...
    ]
    ```
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
        account=account,
        cluster=cluster,
        epoch=epoch,
        submitter=submitter,
        resource=resource,
        age=age,
        summary=summary))

    # report event
    return cls.summarize_report(records)

  def __init__(self, id=None, record=None,
      account=None, cluster=None, epoch=None, submitter=None, resource=None, age=None, summary=None
  ):
    if id or record:
      super().__init__(id=id, record=record)
    else:
      self._resource = resource
      self._age = age
      self._submitter = submitter
      super().__init__(account=account, cluster=cluster, epoch=epoch, summary=summary)

    # now fix up a few special data types
    self._resource = JobResource(self._resource)

  def update_existing_me(self, rec):
    affected = get_db().execute(SQL_UPDATE_BY_ID, (
      self._age, self._submitter, self._id
    )).rowcount

    get_log().debug("Updated oldjob %d with new age %d and submitter %s (%d affected)",
      self._id, self._age, self._submitter, affected)

    return affected == 1

  def find_existing_query(self):
    return (
      "resource = ?",
      [self._resource],
      ('resource', 'age', 'submitter')
    )

  def insert_new(self):
    try:
      get_db().execute(SQL_INSERT_NEW, (
        self._id, self._submitter, self._resource, self._age
      ))
    # TODO: develop normalized exceptions for different database types
    #       except UniqueViolation:
    except Exception:
      get_log().debug("Could not create OldJob record: %s", self.__dict__)
      raise ResourceNotCreated("Unable to create OldJob record")

  @property
  def resource(self):
    return self._resource

  @property
  def users(self):
    return self._submitter

  @property
  def info(self):
    d = super().info
    d['age'] = self._age
    d['resource'] = str(self._resource)
    return d

  def serialize(self, pretty=False, options=None):
    serialized = super().serialize(pretty=pretty, options=options)
    if pretty:
      serialized['resource_pretty'] = str(self._resource)
    return serialized

# register class with reporter registry
registry.register('oldjobs', OldJob)
