# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
import json
from manager.db import get_db
from manager.log import get_log
from manager.ldap import get_ldap
from manager.cluster import Cluster
from manager.otrs import ticket_url

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

# ---------------------------------------------------------------------------
#                                                          reportable class
# ---------------------------------------------------------------------------

class Reportable:
  """
  A base class for reportable trouble metrics.
  """

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
        raise Exception("Could not find {} record with id {}".format(self.__class__.__name__, id))
      self._load_from_rec(rec)
    elif record and not id:
      # factory load
      self._load_from_rec(record)
    else:
      # new report--either a new record or overlaps with existing
      if not epoch or not cluster:
        # TODO: proper exception
        raise BaseException("Cannot create or update reportable without cluster and epoch")

      self._epoch = epoch
      self._cluster = cluster
      self._summary = summary

      # TODO: to handle updating summary, could add that here
      # i.e. if self.update_existing():... but we don't have the record ID, sigh
      if not self.update_existing():

        self._ticket_no = None
        self._ticket_id = None
        self._claimant = None
        self._ticks = 1

        db = get_db()

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

  # should update summary
  def update_existing(self):
    """
    Subclasses must implement this method to verify that an existing, current
    report of a potential issue matching the key data doesn't already exist.

    TODO: This needs to update the ticks, and the epoch, ...
    Returns:
      id of updated record, if there's some way to do that
    """
    raise NotImplementedError

  def insert_new(self):
    """
    Subclasses must implement this method to insert a new record in their
    associated table.  This method is called by the base class after the base
    record has been created in the "reportables" table and an ID is available
    as `self._id`.
    """
    raise NotImplementedError

  @property
  def epoch(self):
    return self._epoch

  @property
  def ticks(self):
    return self._ticks

  @property
  def state(self):
    return self._state

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
