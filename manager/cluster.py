# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=W0621
#
from manager.db import get_db
from manager.exceptions import ResourceNotFound, ResourceNotCreated

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

SQL_DELETE = '''
  DELETE FROM clusters
  WHERE       id = ?
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

def delete_cluster(id):
  db = get_db()
  res = db.execute(SQL_DELETE, (id,))
  if res.rowcount != 1:
    raise ResourceNotFound("Could not find cluster with ID %s" % (id,))
  db.commit()

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
        raise ResourceNotCreated(e) from e
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
