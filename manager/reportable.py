# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
from manager.db import get_db
from manager.log import get_log
from manager.cluster import Cluster

# ---------------------------------------------------------------------------
#                                                               SQL queries
# ---------------------------------------------------------------------------

# use with `.format(tablename)`
SQL_LOOKUP = '''
  SELECT  *
  FROM    {}
  WHERE   id = ?
'''

# use with `.format(tablename, list_of_fields_joined_with_comma,
# list_of_question_marks_matchin_number_of_fields_joined_with_comma)`
SQL_INSERT_NEW = '''
  INSERT INTO {}
              ({})
  VALUES      ({})
'''

# use with `.format(tablename)`
SQL_GET_CURRENT = '''
  SELECT    B.*, COUNT(N.id) AS notes
  FROM      {} B
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

# too complicated, need by cluster
# Not linking in notes yet
SQL_GET_CURRENT_FOR_CLUSTER = '''
  SELECT    B.*, COUNT(N.id) AS notes
  FROM      {} B
  LEFT JOIN notes N
  ON        (B.id = N.burst_id)
  WHERE     cluster = ?
    AND     epoch = (SELECT MAX(epoch) FROM {} WHERE cluster = ?)
  GROUP BY  B.id
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

  def __init__(self, id=None, record=None, cluster=None, epoch=None):
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
      self._epoch = epoch
      self._cluster = cluster

      if not self.update_existing():

        self._state = None
        self._ticket_no = None
        self._ticket_id = None
        self._claimant = None
        self._ticks = 1

        # this would also get the ID and maybe keys() and values() would not
        # return the same order
        #keystr = ', '.join([ k.split('_')[1]) for k in self.__dict__.keys() ])
        #values = self.__dict__.values()
        #qs = len(values) * ('?',)

        keys = []
        values = []
        for k, v in self.__dict__.items():
          if k in ('_id', '_other'):
            continue
          keys.append(k.split('_')[1])
          values.append(v)
        keystr = ', '.join(keys)
        qs = ', '.join(len(values) * ['?'])

        sql = SQL_INSERT_NEW.format(self.__class__._table, keystr, qs)
        get_log().debug("Reportable().__init__: going to execute SQL: %s\nwith values: %s", sql, values)

        self._id = get_db().insert_returning_id(sql, values)

        get_db().commit()

  def _load_from_rec(self, rec):
    for (k, v) in rec.items():
      if k == 'notes':
        self._other = {
          'notes': v
        }
      else:
        self.__dict__['_'+k] = v

  def update_existing(self):
    """
    Subclasses must implement this method to verify that an existing, current
    report of a potential issue matching the key data doesn't already exist.
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

  def serialize(self):
    return {
      key.lstrip('_'): val
      for (key, val) in self.__dict__.items()
    }
