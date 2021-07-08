# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=W0621
#
from manager.db import get_db
from manager.exceptions import ResourceNotFound, DatabaseException

# ---------------------------------------------------------------------------
#                                                               SQL queries
# ---------------------------------------------------------------------------

SQL_CREATE = '''
  INSERT INTO clusters
              (id, name)
  VALUES      (?, ?)
'''

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
    Cluster(rec=row) for row in res
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

  def __init__(self, id=None, name=None, rec=None):

    if rec:
      self.deserialize(rec)
    elif id and not name:
      # lookup
      res = get_db().execute(SQL_GET_BY_ID, (id,)).fetchone()
      if not res:
        raise ResourceNotFound('Could not retrieve cluster "{}"'.format(id))
      self.deserialize(res)
    else:
      # creation
      try:
        get_db().execute(SQL_CREATE, (id, name))
      except Exception as e:
        # TODO: Differentiate between server errors and problems with query
        # (in this case, duplicate records)
        raise DatabaseException(e) from e
      get_db().commit()
      self._id = id
      self._name = name

  @property
  def name(self):
    return self._name

  def deserialize(self, rec):
    for key in rec.keys():
      self.__dict__['_'+key] = rec[key]

  def serialize(self):
    return {
      key.lstrip('_'): val
      for (key, val) in self.__dict__.items()
    }
