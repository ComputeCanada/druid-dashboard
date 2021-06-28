# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=W0621
#
from manager.db import get_db
from manager.exceptions import DatabaseException

# ---------------------------------------------------------------------------
#                                                               SQL queries
# ---------------------------------------------------------------------------

SQL_GET_BY_ID = '''
  SELECT  *
  FROM    clusters
  WHERE   id = ?
'''

SQL_GET_ALL = '''
  SELECT  *
  FROM    clusters
'''

# ---------------------------------------------------------------------------
#                                                             helpers
# ---------------------------------------------------------------------------

def get_clusters():
  res = get_db().execute(SQL_GET_ALL).fetchall()
  if not res:
    return None
  return [
    Cluster(row['id'], row['name']) for row in res
  ]

# ---------------------------------------------------------------------------
#                                                             cluster class
# ---------------------------------------------------------------------------

class Cluster():
  """
  Represents a cluster.

  Attributes:
    _id: id
    _name: proper name of cluster
  """

  def __init__(self, id, name=None):

    self._id = id
    self._name = name

    if not self._name:
      # lookup
      res = get_db().execute(SQL_GET_BY_ID, (self._id,)).fetchone()
      if not res:
        raise DatabaseException('Could not retrieve cluster {}'.format(self._id))
      self._name = res['name']

  @property
  def name(self):
    return self._name

  def serialize(self):
    return {
      key.lstrip('_'): val
      for (key, val) in self.__dict__.items()
    }
