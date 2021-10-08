# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=wrong-import-position,import-outside-toplevel,raise-missing-from
#
"""
Case module: the foundation for reporting problem cases

Subclass the Case class to support a new type of reportable problem
metrics.  The original use case for this was burst candidates: accounts with
significant short-term need that can't be readily met by the resources
typically available without a RAC.

Use the CaseRegistry class to register new case classes so that the
application is aware of them: knows to query them for data to display on the
dashboard and can serve them appropriately via the REST API.

Helper functions provide some common functionality and may be of use to
subclasses.  If creating a utility function for a new subclass, consider
whether it may be of use to other case types.
"""

import re
import json
from inspect import isclass
from flask_babel import _
from manager.log import get_log
from manager.db import get_db
from manager.ldap import get_ldap
from manager.otrs import ticket_url
from manager.cluster import Cluster
from manager.history import History
from manager.exceptions import (
  AppException, BadCall, DatabaseException, ResourceNotFound
)

# ---------------------------------------------------------------------------
#                                                                   helpers
# ---------------------------------------------------------------------------

# regular expression to match job array IDs and allow extraction of just ID
__job_id_re = re.compile(r'^(\d+)')

def just_job_id(jobid):
  """
  Strip job ID to just the base ID, not including any array part.

  Args:
    jobid: Job identifier, optionally including array part.

  Returns:
    Integer job identifier.

  Raises:
    `manager.exceptions.AppException` if the job ID does not match the
    expected format.
  """
  if isinstance(jobid, int):
    return jobid
  match = __job_id_re.match(jobid)
  if not match:
    raise AppException(
      "Could not parse job ID ('{}') to extract base ID".format(jobid)
    )
  return int(match.groups()[0])

def dict_to_table(d):
  """
  Given a dictionary, return a basic HTML table.

  Turns the keys and values of the dictionary into a two-column table where
  the keys are header cells (`TH`) and the values are regular cells (`TD`).
  There is no header row and any complexity in the values are ignored (for
  example there is no hierarchical tabling).

  Args:
    d: A dictionary.

  Returns:
    A basic HTML table to display that dictionary in the simplest possible
    way.
  """
  if not d:
    return ''

  # Create a list of HTML chunks, starting with the beginning representation
  # of a table.  Iterate through the items in the dictionary while appending
  # rows to this list.  Finish the list and return a concatenated string.
  #
  # Starting with a blank or basic string and appending to that can use
  # quadratic time instead of linear time in some cases, so using the list
  # method instead.

  html = ['<table>']
  for k, v in d.items():
    html.append(f"<tr><th>{k}</th><td>{v}</td></tr>")
  html.append('</table>')
  return ''.join(html)

def json_to_table(str):
  """
  Given a JSON string representing a dictionary, return an HTML table.

  See `dict_to_table()` for more detail.

  Args:
    str: A JSON string representation of a dictionary.

  Returns:
    A basic HTML table.
  """
  return dict_to_table(json.loads(str))

# ---------------------------------------------------------------------------
#                                                               SQL queries
# ---------------------------------------------------------------------------

## use with `.format(tablename)`
SQL_LOOKUP = '''
  SELECT    R.ticks, R.account, R.cluster, R.epoch, B.*, R.summary,
            R.claimant, R.ticket_id, R.ticket_no, COUNT(N.id) AS notes
  FROM      reportables R
  JOIN      {} B
  USING     (id)
  LEFT JOIN history N
  ON        (R.id = N.case_id)
  WHERE     R.id = ?
  GROUP BY  R.id, B.id
'''

SQL_INSERT_NEW = '''
  INSERT INTO reportables
              (epoch, account, cluster, summary)
  VALUES      (?, ?, ?, ?)
'''

SQL_UPDATE_BY_ID = '''
  UPDATE  reportables
  SET     ticks = ?,
          epoch = ?,
          summary = ?
  WHERE   id = ?
'''

# Reportable table's columns are explicitly listed to avoid 'id' appearing twice
SQL_GET_CURRENT_FOR_CLUSTER = '''
  SELECT    R.ticks, R.account, R.cluster, R.epoch, B.*, R.summary,
            R.claimant, R.ticket_id, R.ticket_no, COUNT(N.id) AS notes
  FROM      reportables R
  LEFT JOIN {} B
  ON        (R.id = B.id)
  LEFT JOIN history N
  ON        (R.id = N.case_id)
  WHERE     cluster = ?
    AND     epoch = (SELECT MAX(epoch) FROM reportables WHERE cluster = ?) AND R.id IN (SELECT id FROM {})
  GROUP BY  R.id, B.id
'''

# Only query for columns we're not going to overwrite in subsequent update operation.
SQL_FIND_EXISTING = '''
  SELECT    id, R.ticks, {}, R.claimant, R.ticket_id, R.ticket_no
  FROM      reportables R
  LEFT JOIN {} B
  USING     (id)
  WHERE     R.account = ? AND R.cluster = ? AND {}
'''

SQL_SET_TICKET = '''
  UPDATE  reportables
  SET     ticket_id = ?, ticket_no = ?
  WHERE   id = ?
'''

SQL_GET_APPROPRIATE_TEMPLATES = '''
  SELECT    template
  FROM      appropriate_templates
  WHERE     enabled = TRUE AND casetype = ?
'''

# ---------------------------------------------------------------------------
#                                                         Case registry
# ---------------------------------------------------------------------------

class CaseRegistry:
  """
  Singular registry of case classes.

  The application uses this registry to query available case types.  Subclasses
  of the Case class register so the application is aware of them and knows to
  query and present different case types.  A global instance of the registry is
  created on module initialization.

  Basic usage:

  ```
  # register class with reporter registry
  registry.register('bursts', Burst)
  ```

  Attributes:
    reporters: Dict of case names to their classes.
  """

  _instance = None

  def __new__(cls):
    if cls._instance is not None:
      raise BadCall("Cannot create two instances of this class.  Use get_registry()")
    cls._instance = super(CaseRegistry, cls).__new__(cls)
    return cls._instance

  @classmethod
  def get_registry(cls):
    """Return singular instance of registry."""

    if cls._instance is None:
      cls._instance = cls()
    return cls._instance

  def __init__(self):
    self._reporters = {}
    self._descriptions = {}

  def register(self, name, reporter):
    """
    Register a Case implementation.

    Subclasses of the `Case` class must register themselves so the application
    knows to query these classes.  A subclass of the Case class must use this
    method at the end of its module file.

    Args:
      name: The common name for the reporter type.  This name will be used,
        for example, when reporting via the API.  It is recommended it match
        the table name and be plural, for example, "bursts" or "oldjobs".
      reporter: The subclass.

    Raises:
      `manager.exceptions.AppException` if a reporter with that name has
        already by registered.
    """
    if name in self._reporters.keys():
      raise AppException("A reporter has already been registered with that name: {}".format(name))
    if not isclass(reporter) or not issubclass(reporter, Case):
      raise AppException("The reporter is not a subclass of Case")
    description = reporter.describe()

    # register
    self._reporters[name] = reporter
    self._descriptions[name] = description
    get_log().info("Registered reporter for %s", name)

  def deregister(self, name):
    """
    Deregister a Case implementation.

    This method should only be used in testing where a nonsense or half-
    implemented Case subclass is registered but should not be considered for
    subsequent testing.  As such, trying to register an unregistered reporter
    is not an error and will not throw an exception.

    Args:
      name: The name for the reporter used when registering it.
    """
    try:
      del self._reporters[name]
      del self._descriptions[name]
    except KeyError:
      pass

  @property
  def reporters(self):
    """Dictionary of reporter name to class."""
    return self._reporters

  @property
  def descriptions(self):
    """
    Dictionary of reporter name to the data description provided by the
    reporter.
    """
    return self._descriptions

# create global reporter registry
registry = CaseRegistry.get_registry()

# ---------------------------------------------------------------------------
#                                                       base Case class
# ---------------------------------------------------------------------------

class Case:
  """
  Base class for reportable metrics of concern.

  The Case class defines methods or stubs necessary to support representing
  and reporting potential problem cases.

  Subclasses of this class implement a single instance of a reportable case.
  For example, an instance of the OldJob class represents an account on a
  cluster with really old jobs.  Tomorrow if that account still has really old
  jobs, it'll be reported again (via the appropriate subclass of
  `manager.reporter.Reporter`) but it will still be the same instance, though
  some of the details may change.

  Instances of these subclasses are represented in the database by a row in
  each of two tables: the reportables table, which stores information common
  to all types, and in a table specific to the subclass.

  Additionally subclasses define methods for reporting and presenting problem
  cases.

  Subclasses must implement some methods and may override others, as
  documented.  Methods implemented here merely as stubs will throw
  `NotImplementedError` if called.
  """

  @classmethod
  def describe(cls):
    """
    Describe report structure and semantics.

    The results of this method are used to meaningfully present the report data
    (provided by other methods).  For example, these descriptions can be used
    to inform UI templates what columns should appear in the report table on
    the Dashboard.

    The data returned has the following structure:
    ```
    {
      table: str,       # table name in database
      title: str,       # display title of report
      metric: str,      # primary metric of interest
      cols: [{          # ordered list of field descriptors
        datum: ..,      # name of reported data field
        title: ..,      # display label (such as for column header)
        searchable: .., # should column data be included in searches
        sortable: ..,   # should table be sortable on this column
        type: ..,       # type (text or number, used for display)
        help: ..        # help text, displayed when hovering over title
      }, ... ],
    }
    ```

    Returns:
      A data structure conforming to the above.

    Note:
      Subclasses _must not_ override this function.  Instead, subclasses
      _must_ override `Case.describe_me()` to describe the specifics of
      that case and this method will combine the common and specific field
      descriptions.
    """
    desc = cls.describe_me()
    desc['table'] = cls._table
    desc['cols'].insert(0,
      { 'datum': 'ticks',
        'searchable': False,
        'sortable': True,
        'type': 'number',
        'title': "<img src='static/icons/ticks.svg' height='18' width='20' " \
                 "alt='Times reported' title='Times reported'/>",
      }
    )
    desc['cols'].insert(1,
      { 'datum': 'account',
        'searchable': True,
        'sortable': True,
        'type': 'text',
        'title': _('Account')
      }
    )
    desc['cols'].extend([
      { 'datum': 'summary',
        'searchable': True,
        'sortable': False,
        'type': 'text',
        'title': _('Summary')
      },
      { 'datum': 'claimant',
        'searchable': True,
        'sortable': True,
        'type': 'text',
        'title': _('Analyst')
      },
      { 'datum': 'ticket',
        'searchable': True,
        'sortable': True,
        'type': 'text',
        'title': _('Ticket')
      },
      { 'datum': 'notes',
        'searchable': False,
        'sortable': True,
        'type': 'text',
        'title': _('Notes')
      },
      { 'datum': 'action',
        'searchable': False,
        'sortable': False,
        'type': 'text',
        'title': _('Action')
      }
    ])

    return desc

  @classmethod
  def describe_me(cls):
    """
    Describe report structure and semantics specific to case type.

    Subclasses should implement this to describe the table name, report title,
    and the primary metric of the case type as well as columns specific to
    and implemented by the subclass.  The Case class will call this method
    from `Case.describe()` to generate the full report.

    All fields are required with the exception of `help`.

    The data returned has the following structure:
    ```
    {
      table: str,       # table name in database
      title: str,       # display title of report
      metric: str,      # primary metric of interest
      cols: [{          # ordered list of field descriptors
        datum: ..,      # name of reported data field
        title: ..,      # display label (such as for column header)
        searchable: .., # should column data be included in searches
        sortable: ..,   # should table be sortable on this column
        type: ..,       # type (text or number, used for display)
        help: ..        # help text, displayed when hovering over title
      }, ... ],
    }
    ```

    Returns:
      A data structure conforming to the above.
    """
    raise NotImplementedError

  @classmethod
  def summarize_report(cls, cases):
    """
    Provide a brief, one-line summary of last report.

    The intended use case for this summary is for notifications, such as to
    Slack, when a report is received and interpreted.

    Subclasses may override this method to provide additional information.

    Args:
      cases: The list of cases created or updated from the last report.

    Returns:
      A string description of the last report.
    """
    claimed = 0
    newbs = 0
    existing = 0

    for case in cases:
      if case.claimant is not None:
        claimed += 1
      if case.ticks > 1:
        existing += 1
      else:
        newbs += 1
    return f"There are {len(cases)} cases ({newbs} new and {existing} existing).  {claimed} are claimed."

  @classmethod
  def report(cls, cluster, epoch, data):
    """
    Report potential job and/or account issues.

    Subclasses must implement this to interpret reports coming through the API
    from a Detector.  Those implementations should describe the expected
    format of the `data` argument and should call `Case.summarize_report()`
    to provide a summary as return value.

    Args:
      cluster: The reporting cluster.
      epoch: Epoch of report (UTC).
      data: A list of dicts describing current instances of potential account
            or job pain or other metrics, as appropriate for the type of
            report.

    Returns:
      String describing summary of report.
    """
    raise NotImplementedError

  @classmethod
  def view(cls, criteria):
    """
    Provide view to reported data.

    By default, provides current view of reported data.  Subclasses may
    override this to provide additional views.

    The view is described as follows:
    ```
    epoch: seconds since epoch
    results:
      - obj1.attribute1: ..
        obj1.attribute2: ..
        obj1.attribute2_pretty: ..
        obj1.attribute3: ..
        ...
      - obj2.attribute1: ..
        obj2.attribute2: ..
        obj2.attribute2_pretty: ..
        obj2.attribute3: ..
        ...
      ...
    ```

    Attributes suffixed with `_pretty` provide display versions of those
    attributes without, if appropriate and requested.

    Args:
      criteria: Dict of criteria for selecting data for view.  In this
      implementation, `cluster` is required and `pretty` is optional.
        * `cluster`: (required) Cluster for which to provide data.
        * `pretty`: (optional, default False): provide display-friendly
          alternatives on some fields, if possible.

    Returns:
      None or a data structure conforming to the above.

    Raises:
      NotImplementedError: Criteria other than `pretty` or `cluster` were
        specified, indicating this method should have been overridden by a
        subclass and was not.
    """

    # 'cluster' required, 'pretty' optional, nothing else handled
    if set(criteria.keys()) - {'pretty'} != {'cluster'}:
      raise NotImplementedError

    records = cls.get_current(criteria['cluster'])
    if not records:
      return None
    epoch = records[0].epoch

    pretty = criteria.get('pretty', False)

    # serialize records individually so as to add attributes
    serialized = [
      rec.serialize(pretty=pretty) for rec in records
    ]

    return {
      'epoch': epoch,
      'results': serialized
    }

  @classmethod
  def get(cls, id):
    """
    Find and load the appropriate Case object given the ID.

    Case IDs are unique among all subclasses.  In the database, they are
    stored in the common reportables table and referenced from the
    subclass-specific table.

    This implementation tries to instantiate each of the registered case
    classes using the given ID.  This is not efficient or graceful.

    Args:
      id: The numeric ID of the case.

    Returns:
      An instance of the appropriate case class with that ID, or None.
    """

    # TODO: This could be improved by having a bidirectional link--such as
    #       storing the subclass report type in the reportables table

    registry = CaseRegistry.get_registry()

    # try to instantiate appropriate subclass by going through each in turn
    for reportercls in registry.reporters.values():
      try:
        return reportercls(id=id)
      except ResourceNotFound:
        pass

    get_log().error("Could not find reporter class for case ID %d", id)
    return None

  @classmethod
  def get_current(cls, cluster):
    """
    Get the current cases for this type of report.

    Args:
      cluster: The identifier for the cluster of interest.

    Returns:
      A list of appropriate case objects, or None.
    """
    res = get_db().execute(
      SQL_GET_CURRENT_FOR_CLUSTER.format(cls._table, cls._table),
      (cluster, cluster)
    ).fetchall()
    if not res:
      return None
    return [
      cls(record=rec) for rec in res
    ]

  @classmethod
  def set_ticket(cls, id, ticket_id, ticket_no):
    """
    Set the ticket information for a given case ID.

    This is a convenience function that avoids actually finding and
    instantiating the matching case.

    Args:
      id: The case ID.
      ticket_id: The OTRS ticket ID.
      ticket_no: The OTRS ticket number.

    Raises:
      DatabaseException if the execution fails.

    Notes:
      The ticket ID and number are confusing and meaningful only to OTRS.
      The Dude abides.
    """
    db = get_db()
    res = db.execute(SQL_SET_TICKET, (ticket_id, ticket_no, id))

    # TODO: should use rowcount == 1 instead of res
    if not res:
      raise DatabaseException("Could not set ticket information for case ID {}".format(id))
    db.commit()

  @classmethod
  def appropriate_templates(cls):
    """
    Return a list of templates appropriate for this type of case.

    Returns:
      A list of templates appropriate for this type of case.
    """
    db = get_db()
    res = db.execute(SQL_GET_APPROPRIATE_TEMPLATES, (cls._table,)).fetchall()
    get_log().debug("Retrieving appropriate templates for %s: %s", cls._table, res)
    if not res:
      return None
    return [
      rec['template'] for rec in res
    ]

  def __init__(self,
      id=None, record=None,
      account=None, cluster=None, epoch=None, summary=None
    ):
    """
    There are three modes for creating a Case object:

    1.  Lookup by ID.  Specify the ID but NOT the record.
    2.  Factory loading by specifying a database record (row).  Specify the
        record but not the ID.
    3.  Creating a "new" Case specifying information about it.  Note that it
        may be that an existing case is found matching enough of the
        information to be effectively the same case.  Both `id` and `record`
        should not be set.

    Subclasses will need to override this method but _must_ invoke the base
    implementation via `super().__init__()` to ensure the entire object is
    initialized and persisted.

    Args:
      id: Unique identifier for the case.
      record: Dictionary describing all the values for the case.  This is used
        to efficiently instantiate multiple objects from a multiple-row query,
        or other examples of factory loading.
      cluster: The cluster where this case occurred.
      epoch: The UNIX epoch (UTC) when this case was (last) reported.
      summary: A dictionary of arbitrary information supplied by the Detector
        which may be of use to analysts in addressing the case.

    Raises:
      `manager.exceptions.ResourceNotFound` if the ID (but no record) is
        supplied and no record with that ID can be found.
      `manager.exceptions.BadCall` if a nonsensical combination of named
        arguments are supplied.
    """

    if id and not record:
      # lookup record
      rec = get_db().execute(
        SQL_LOOKUP.format(self.__class__._table), (id,)
      ).fetchone()
      if not rec:
        raise ResourceNotFound("Could not find {} record with ID {}".format(self.__class__.__name__, id))
      self._load_from_rec(dict(rec))
    elif record and not id:
      # factory load
      self._load_from_rec(dict(record))
    else:
      # new report--either a new record or overlaps with existing
      if not epoch or not cluster:
        raise BadCall("Cannot create or update Case without cluster and epoch")

      self._epoch = epoch
      self._account = account
      self._cluster = cluster
      self._summary = summary
      db = get_db()

      # update existing record if possible, if not...
      if not self.update_existing():

        self._ticket_no = None
        self._ticket_id = None
        self._claimant = None
        self._ticks = 1

        self._id = db.insert_returning_id(SQL_INSERT_NEW,
          (self._epoch, self._account, self._cluster, json.dumps(self._summary)
          ))
        self.insert_new()

      db.commit()

  def _load_from_rec(self, rec):
    """
    Helper method for initializing an object given a dictionary describing its
    attributes.
    """
    for (k, v) in rec.items():
      if k == 'notes':
        self._other = {
          'notes': v
        }
      elif k == 'summary':
        self._summary = json.loads(v) if v else None
      else:
        self.__dict__['_'+k] = v

  def find_existing_query(self):
    """
    Returns partial query and terms to complete the SQL_FIND_EXISTING query.
    Essentially, query and terms are used to complete the WHERE clause begun
    with `WHERE cluster = ? AND`.

    Subclasses MUST implement this to enable detection of when a reported
    record matches one already in the database.

    Returns:
      A tuple (query, terms, cols) where:
        - `query` (string) completes the WHERE clauses in SQL_FIND_EXISTING,
        - `terms` (list) lists the search terms in the query, and
        - `cols` (list) lists the columns included in the selection.
    """
    raise NotImplementedError

  def update_existing_me(self, rec):
    """
    Updates the subclass's partial record of an existing case.  Subclasses
    must implement this to write to the database the appropriate values of
    a case's latest report.

    Args:
      rec (dict or dict-like object depending on database type): details
        about the existing record (NOT the updated data which was used to
        initialize the case object).  The implementation decides what in the
        record should update the local object, and updates the persistent
        object with new data as appropriate.
    """
    raise NotImplementedError

  def update_existing(self):
    """
    Handle updates to existing records.  This is called on initialization
    to handle existing cases, as partially defined by subclasses (see
    `find_existing_query()`).  Updates are also handled by subclass (see
    `update_existing_me()`).

    At this point this is called, self should be initialized with the
    details provided, but this may need to be appropriately adjusted with
    data from the matching case in the database.

    Returns:
      A boolean indicating whether there was a record to update.
    """
    (query, terms, columns_list) = self.find_existing_query()

    # turn list of column names into "B.col1, B.col2, ..."
    columns_str = ", ".join(map(lambda x: "B." + x, columns_list))

    rec = get_db().execute(
      SQL_FIND_EXISTING.format(columns_str, self.__class__._table, query),
      [self._account, self._cluster] + list(terms)
    ).fetchone()
    if not rec:
      return False

    # populate self as appropriate.  Currently only has data from report
    self._ticks = rec['ticks'] + 1
    for col in ['id', 'claimant', 'ticket_id', 'ticket_no']:
      self.__dict__['_'+col] = rec[col]
    try:
      if not self.update_existing_me(rec):
        return False
    except NotImplementedError:
      raise NotImplementedError("Subclass has not implemented required methods")
    except BaseException as e:
      raise BadCall("Could not update case %d (%s): %s" % (
        self._id, self.__class__.__name__, e.__class__.__name__,)
      )

    affected = get_db().execute(SQL_UPDATE_BY_ID, (
      self._ticks, self._epoch, json.dumps(self._summary), self._id
    )).rowcount

    return affected == 1

  def insert_new(self):
    """
    Subclasses must implement this method to insert a new record in their
    associated table.  This method is called by the base class after the base
    record has been created in the "reportables" table and an ID is available
    as `self._id`, which the subclass can use in the database to link records
    in its table to the reportables table.
    """
    raise NotImplementedError

  def update(self, update, who):
    """
    Updates the appropriate record for a new note, change to claimant, etc.
    Subclasses can implement this to intercept the change, such as to make a
    value database-friendly, but should pass the execution back to the super
    class which will execute the SQL statement.

    A history record is created for the update.

    Args:
      update: A dict with `note` and/or `datum` and `value` defined describing
        the update.
      who: The CCI of the individual carrying out the change, that is, the
        logged-in user.
    """

    was = None
    now = None
    what = update.get('datum', None)
    if what:
      if what == 'claimant':
        table = 'reportables'
      else:
        table = self.__class__._table

      was = self.serialize()[what]
      now = update['value']

      get_log().debug("Updating case %d, %s: %s => %s", self._id, what, was, now)

      # update self locally and persistently
      self.__dict__['_'+what] = now
      query = "UPDATE {} SET {} = ? WHERE id = ?".format(table, what)
      get_log().debug("Going to execute '%s' with (%s, %d)", query, now, self._id)
      affected = get_db().execute("UPDATE {} SET {} = ? WHERE id = ?".format(table, what), (now, self._id)).rowcount
      get_db().commit()
      get_log().debug("Rows affected: %d", affected)

    text = update.get('note', None)
    timestamp = update.get('timestamp', None)

    # record update in history
    History(caseID=self._id, analyst=who, timestamp=timestamp, text=text, datum=what, was=was, now=now)

  @property
  def id(self):
    """
    The numerical identifier of this case, assigned by the database as an
    auto-incrementing sequence.
    """
    return self._id

  @property
  def account(self):
    """
    The account associated with this case.
    """
    return self._account

  @property
  def cluster(self):
    """
    The cluster where this case originated.
    """
    return self._cluster

  @property
  def epoch(self):
    """
    The most recent UNIX epoch (UTC) this case was reported.
    """
    return self._epoch

  @property
  def ticks(self):
    """
    The number of reports including this case.
    """
    return self._ticks

  @property
  def ticket_id(self):
    """
    The primary ticket identifier.  Numeric.
    """
    return self._ticket_id

  @property
  def ticket_no(self):
    """
    The other primary ticket identifier.  Looks numeric.  Is not the same as
    `ticket_id`.  Actually a string.
    """
    return self._ticket_no

  @property
  def claimant(self):
    """
    The analyst that has signalled they will pursue this case.
    """
    return self._claimant

  @property
  def notes(self):
    """
    Notes associated with this case.
    """
    if self._other and 'notes' in self._other:
      return self._other['notes']
    return None

  @property
  def info(self):
    """
    Some information about this case, used for passing on to templates.
    """
    d = {
      'type': self._table,
      'account': self._account,
      'cluster': Cluster(self._cluster).name,
      'resource': self._resource,
      'users': self.users
    }
    if self._summary:
      d['summary'] = self._summary
    return d

  @property
  def users(self):
    """
    User contacts for this potential issue.

    This can depend on the type of issue: a PI is responsible for use of the
    account, so the PI should be the contact for questions of resource
    allocation.  For a misconfigured job, the submitting user is probably more
    appropriate.

    The PI is always included and derived from the account associated with the
    case.  This method should return all usernames associated with the case,
    such as those submitting problematic jobs, and so on.

    Order is preserved and can be used to suggest defaults.
    """
    raise NotImplementedError

  def serialize(self, pretty=False, options=None):
    """
    Provide a dictionary representation of self.

    By default, simply returns a dictionary of attributes with leading
    underscores removed.  If `pretty` is specified, the dictionary may be
    augmented with prettified versions of some attributes, depending on the
    implementation.  In the base implementation, prettification includes:

    * `claimant_pretty` is included if the value for `claimant` is found in
      LDAP and will be set to the person's given name.
    * `ticket` is included if `ticket_id` is set and becomes an HTML anchor
      element for that ticket.
    * `summary_pretty` is included if `summary` is set,
      `options['skip_summary_prettification']` is either unset or false, and
      is populated with an HTML table interpretation of the summary attribute.

    In general, prettified attributes should compliment, not replace, the
    originals, and the consumer may choose.

    Subclasses may override this to provide their own prettification, and must
    must call `super().serialize(...)` appropriately to ensure full
    representation.  See existing subclasses for examples.

    Args:
      pretty: if True, prettify some fields
      options: optional dictionary of options

    Returns:
      A dictionary representation of the case.
    """

    dct = {
      key.lstrip('_'): val
      for (key, val) in self.__dict__.items()
    }
    if pretty:

      # add claimant's name
      if self._claimant:
        person = get_ldap().get_person_by_cci(self._claimant)
        if not person:
          get_log().error("Could not find name for cci '%s'", self._claimant)
        else:
          dct['claimant_pretty'] = person['givenName']

      # add ticket URL if there's a ticket
      if self._ticket_id:
        dct['ticket'] = "<a href='{}' target='_ticket'>{}</a>".format(ticket_url(self._ticket_id), self._ticket_no)
      else:
        dct['ticket'] = None

      # turn summary into table
      if self._summary and (options is None or not options.get('skip_summary_prettification', False)):
        dct['summary_pretty'] = dict_to_table(self._summary)

    return dct
