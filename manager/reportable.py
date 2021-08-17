# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=raise-missing-from
#
"""
Reportable class for implementing new types of problem metrics.
"""

import json
from manager.db import get_db
from manager.log import get_log
from manager.ldap import get_ldap
from manager.cluster import Cluster
from manager.otrs import ticket_url
from manager.reporter import ReporterRegistry
from manager.exceptions import DatabaseException, BadCall, ResourceNotFound
from manager.history import History

# ---------------------------------------------------------------------------
#                                                                   helpers
# ---------------------------------------------------------------------------

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
  SELECT    R.ticks, R.cluster, R.epoch, B.*, R.summary, R.claimant, R.ticket_id, R.ticket_no, COUNT(N.id) AS notes
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
              (epoch, cluster, summary)
  VALUES      (?, ?, ?)
'''

SQL_GET_BY_ID = '''
  SELECT  *
  FROM    reportables
  WHERE   id = ?
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
  SELECT    R.ticks, R.cluster, R.epoch, B.*, R.summary, R.claimant, R.ticket_id, R.ticket_no, COUNT(N.id) AS notes
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
  WHERE     R.cluster = ? AND {}
'''

SQL_SET_TICKET = '''
  UPDATE  reportables
  SET     ticket_id = ?, ticket_no = ?
  WHERE   id = ?
'''

# ---------------------------------------------------------------------------
#                                                          reportable class
# ---------------------------------------------------------------------------

class Reportable:
  """
  A base class for reportable trouble metrics.

  Subclasses of this class implement a single instance of a reportable case.
  For example, an instance of the OldJob class represents an account on a
  cluster with really old jobs.  Tomorrow if that account still has really old
  jobs, it'll be reported again (via the appropriate subclass of
  `manager.reporter.Reporter`) but it will still be the same instance, though
  some of the details may change.

  Instances of these subclasses are represented in the database by a row in
  each of two tables: the reportables table, which stores information common
  to all types, and in a table specific to the subclass.

  Subclasses must implement some methods and may override others, as
  documented.  Methods implemented here merely as stubs will throw
  `NotImplementedError` if called.
  """

  @classmethod
  def get(cls, id):
    """
    Find and load the appropriate Reportable object given the ID.

    Reportable IDs are unique among all subclasses.  In the database, they are
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

    # TODO: This assumes every Reporter also implements Reportable.  Really
    #       should just merge them into "Case".

    registry = ReporterRegistry.get_registry()

    # try to instantiate reportable's subclass by going through each in turn
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
      A list of appropriate reportable objects, or None.
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

  def __init__(self, id=None, record=None, cluster=None, epoch=None, summary=None):
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
        raise BadCall("Cannot create or update Reportable without cluster and epoch")

      self._epoch = epoch
      self._cluster = cluster
      self._summary = summary
      db = get_db()

      # update existing record if possible, if not...
      if not self.update_existing():

        self._ticket_no = None
        self._ticket_id = None
        self._claimant = None
        self._ticks = 1

        self._id = db.insert_returning_id(SQL_INSERT_NEW, (self._epoch, self._cluster, json.dumps(self._summary)))
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

  def _update_existing_sub(self, rec):
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
    `find_exsiting_query()`).  Updates are also handled by subclass (see
    `_update_existing_sub()`).

    At this point this is called, self should be initialized with the
    details provided, but this may need to be appropriately adjusted with
    data from the matching case in the database.

    Returns: boolean indicating whether there was a record to update
    """
    (query, terms, columns_list) = self.find_existing_query()

    # turn list of column names into "B.col1, B.col2, ..."
    columns_str = ", ".join(map(lambda x: "B." + x, columns_list))

    rec = get_db().execute(
      SQL_FIND_EXISTING.format(columns_str, self.__class__._table, query),
      [self._cluster] + list(terms)
    ).fetchone()
    if not rec:
      return False

    # populate self as appropriate.  Currently only has data from report
    self._ticks = rec['ticks'] + 1
    for col in ['id', 'claimant', 'ticket_id', 'ticket_no']:
      self.__dict__['_'+col] = rec[col]
    try:
      if not self._update_existing_sub(rec):
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
    basic = {
      'account': self._account,
      'cluster': Cluster(self._cluster).name,
      'resource': self._resource,
    }
    if self._summary:
      return dict(basic, **self._summary)
    return basic

  @property
  def contact(self):
    """
    Contact information for this potential issue.

    This can depend on the type of issue: a PI is responsible for use of the
    account, so the PI should be the contact for questions of resource
    allocation.  For a misconfigured job, the submitting user is probably more
    appropriate.
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
