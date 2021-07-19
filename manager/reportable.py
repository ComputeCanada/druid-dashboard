# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
import json
from manager.db import get_db
from manager.log import get_log
from manager.ldap import get_ldap
from manager.cluster import Cluster
from manager.otrs import ticket_url
from manager.reporter import ReporterRegistry
from manager.exceptions import DatabaseException, BadCall
from manager.actions import Update

# ---------------------------------------------------------------------------
#                                                               SQL queries
# ---------------------------------------------------------------------------

# use with `.format(tablename)`
SQL_LOOKUP = '''
  SELECT  *
  FROM    reportables
  JOIN    {}
  USING   (id)
  WHERE   id = ?
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
  LEFT JOIN notes N
  ON        (R.id = N.burst_id)
  WHERE     cluster = ?
    AND     epoch = (SELECT MAX(epoch) FROM reportables WHERE cluster = ? AND id IN (SELECT id FROM {}))
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

# ---------------------------------------------------------------------------
#                                                          reportable class
# ---------------------------------------------------------------------------

class Reportable:
  """
  A base class for reportable trouble metrics.
  """

  @classmethod
  def get(cls, id):
    # TODO: this is extreme janketiness
    # try to instantiate reportable's subclass by going through each in turn
    get_log().debug("Here in %s.get(%d)", cls, id)
    registry = ReporterRegistry.get_registry()

    for (name, reportercls) in registry.reporters.items():
      get_log().debug("Trying %s/%s for ID %d", name, reportercls, id)
      try:
        return reportercls(id=id)
      except DatabaseException:
        pass
    raise DatabaseException("Could not find appropriate case with ID {}".format(id))

  @classmethod
  def get_current(cls, cluster):
    res = get_db().execute(SQL_GET_CURRENT_FOR_CLUSTER.format(cls._table, cls._table), (cluster, cluster)).fetchall()
    if not res:
      get_log().debug("Did not find any records in %s", cls._table)
      return None
    get_log().debug("Returning records for %s", cls._table)
    return [
      cls(record=rec) for rec in res
    ]

  def __init__(self, id=None, record=None, cluster=None, epoch=None, summary=None):
    if id and not record:
      # lookup record
      rec = get_db().execute(
        SQL_LOOKUP.format(self.__class__._table), (id,)
      ).fetchone()
      if not rec:
        # TODO: evaluate if this type of exception should be used here
        raise DatabaseException("Could not find {} record with id {}".format(self.__class__.__name__, id))
      self._load_from_rec(dict(rec))
    elif record and not id:
      # factory load
      self._load_from_rec(dict(record))
    else:
      # new report--either a new record or overlaps with existing
      if not epoch or not cluster:
        # TODO: proper exception
        raise BaseException("Cannot create or update reportable without cluster and epoch")

      self._epoch = epoch
      self._cluster = cluster
      self._summary = summary
      db = get_db()

      # TODO: to handle updating summary, could add that here
      # i.e. if self.update_existing():... but we don't have the record ID, sigh
      if not self.update_existing():

        get_log().debug(
          "Creating new reportable with cluster=%s, epoch=%s, summary=%s",
           cluster, epoch, summary
        )
        self._ticket_no = None
        self._ticket_id = None
        self._claimant = None
        self._ticks = 1

        self._id = db.insert_returning_id(SQL_INSERT_NEW, (self._epoch, self._cluster, json.dumps(self._summary)))
        self.insert_new()

      db.commit()

  def _load_from_rec(self, rec):
    for (k, v) in rec.items():
      if k == 'notes':
        self._other = {
          'notes': v
        }
      else:
        self.__dict__['_'+k] = v

  def find_existing_query(self):
    """
    Returns partial query and terms to complete the SQL_FIND_EXISTING query,
    above.

    Returns: (query, terms) where:
      query (string) completes the WHERE clauses in SQL_FIND_EXISTING.
      terms (list) lists the search terms in the query,
      cols (list) lists the columns include in the selection
    """
    raise NotImplementedError

  def _update_existing_sub(self, rec):
    raise NotImplementedError

  def update_existing(self):
    """
    TODO: this documentation is not correct

    At this point self should be loaded with all the in-DB information.  The
    only stuff that needs updating is the stuff that can change in the given
    case.

    Subclasses must implement this method to verify that an existing, current
    report of a potential issue matching the key data doesn't already exist.

    Returns: boolean indicating whether there was a record to update
    """
    (query, terms, columns_list) = self.find_existing_query()

    # turn list of column names into "B.col1, B.col2, ..."
    columns_str = ", ".join(map(lambda x: "B." + x, columns_list))
    get_log().debug("Columns to update local object with: '%s'", columns_str)

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
    as `self._id`.
    """
    raise NotImplementedError

  def _interpret_update(self, datum, was, now):
    """
    Subclasses should implement this for datums they handle specifically.
    Common datums such as claimant and notes can be handled by the base
    class but others such as state must be handled by the subclass.
    """
    # TODO: implement

  def get_history(self):
    # find all updates relating to this reportable and return... what?
    # printing off "I am self" to avoid lint warning for now
    get_log().debug("Updating history... (not really), I am %s", self.__class__.__name__)

  def update(self, update, who):

    what = update['datum']
    if what == 'claimant':
      table = 'reportables'
    else:
      table = self.__class__._table

    was = self.serialize()[what]
    now = update['value']
    text = update.get('note', None)
    timestamp = update.get('timestamp', None)

    get_log().debug("Updating case %d, %s: %s => %s", self._id, what, was, now)

    # update self locally and persistently
    self.__dict__['_'+what] = now
    query = "UPDATE {} SET {} = ? WHERE id = ?".format(table, what)
    get_log().debug("Going to execute '%s' with (%s, %d)", query, now, self._id)
    affected = get_db().execute("UPDATE {} SET {} = ? WHERE id = ?".format(table, what), (now, self._id)).rowcount
    get_db().commit()
    get_log().debug("Rows affected: %d", affected)

    # record update in history
    Update(caseID=self._id, analyst=who, timestamp=timestamp, text=text, datum=what, was=was, now=now)

  @property
  def id(self):
    return self._id

  @property
  def epoch(self):
    return self._epoch

  @property
  def ticks(self):
    return self._ticks

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
    }
    if self._summary:
      return dict(basic, **self._summary)
    return basic

  @property
  def contact(self):
    """
    Return contact information for this potential issue.  This can depend on
    the type of issue: a PI is responsible for use of the account, so the PI
    should be the contact for questions of resource allocation.  For a
    misconfigured job, the submitting user is probably more appropriate.

    Returns: username of contact.
    """
    raise NotImplementedError

  def serialize(self, pretty=False):
    get_log().debug("Serializing myself: %s (pretty = %s) dict = %s", self.__class__.__name__, pretty, self.__dict__)
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
          dct['claimant_pretty'] = person['givenname']

      # add ticket URL if there's a ticket
      if self._ticket_id:
        dct['ticket'] = "<a href='{}' target='_ticket'>{}</a>".format(ticket_url(self._ticket_id), self._ticket_no)
      else:
        dct['ticket'] = None

    return dct
