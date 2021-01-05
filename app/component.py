# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=W0621
#
from app.db import get_db
from app.exceptions import DatabaseException
from app.apikey import most_recent_use

# ---------------------------------------------------------------------------
#                                                               SQL queries
# ---------------------------------------------------------------------------

SQL_GET = '''
  SELECT    name, cluster, service
  FROM      components
  WHERE     id = ?
'''

SQL_GET_ALL = '''
  SELECT  id, name, cluster, service
  FROM    components
'''

SQL_CREATE_NEW = '''
  INSERT INTO components
              (id, name, cluster, service)
  VALUES      (?, ?, ?, ?)
'''

SQL_DELETE = '''
  DELETE FROM components
  WHERE       id = ?
'''

SQL_UPDATE_NAME = '''
  UPDATE  components
  SET     name = ?
  WHERE   id = ?
'''

# ---------------------------------------------------------------------------
#                                                                   helpers
# ---------------------------------------------------------------------------


def get_components(get_last_heard=False):
  db = get_db()
  res = db.execute(SQL_GET_ALL).fetchall()
  if not res:
    return None
  components = []
  for row in res:
    components.append(Component(
      id=row['id'],
      name=row['name'],
      cluster=row['cluster'],
      service=row['service'],
      factory_load=True,
      get_last_heard=get_last_heard
    ))
  return components


def add_component(id, name, cluster, service):
  return Component(id, name, cluster, service)


def delete_component(id):
  db = get_db()
  db.execute(SQL_DELETE, (id,))
  db.commit()


# ---------------------------------------------------------------------------
#                                                           component class
# ---------------------------------------------------------------------------

class Component():
  """
  Represents a unique component.

  Attributes:
    _id: id
    _name: name
    _cluster: cluster
    _service: service
    _lastheard: lastheard
  """

  def __init__(self, id, name=None, cluster=None, service=None, get_last_heard=False, factory_load=False):

    self._id = id
    self._name = name
    self._cluster = cluster
    self._service = service
    self._lastheard = None

    # handle instantiation by factory
    if factory_load:
      if get_last_heard:
        self.load_lastheard()
      return

    # creating or retrieving?
    db = get_db()
    if id and not name:
      res = db.execute(SQL_GET, (id,)).fetchone()
      if res:
        self._name = res['name']
        self._cluster = res['cluster']
        self._service = res['service']
        if get_last_heard:
          self.load_lastheard()
      else:
        raise ValueError(
          "Could not load component with id '{}'".format(id)
        )
    else:
      if not cluster and not service:
        # update component name
        try:
          db.execute(SQL_UPDATE_NAME, (name, id))
          db.commit()
        except Exception as e:
          raise DatabaseException(
            "Could not execute SQL_UPDATE_NAME for {}, name='{}'".format(
              id, name
            )
          ) from e
      elif not cluster or not service:
        # TODO: this exception is a pile of worms in a police uniform
        raise Exception("Specify id, id and name, or id, name, cluster and service")
      try:
        db.execute(SQL_CREATE_NEW, (id, name, cluster, service))
        db.commit()
      except Exception as e:
        raise DatabaseException(
          "Could not execute SQL_CREATE_NEW with "
          "id='{}', name='{}', cluster='{}', service='{}' ('{}')".format(
            id, name, cluster, service, e
          )
        ) from e

  def load_lastheard(self):
    # query related API keys for most recently used
    self._lastheard = most_recent_use(self._id)

  @property
  def lastheard(self):
    if not self._lastheard:
      self.load_lastheard()
    return self._lastheard

  def serializable(self):
    return {
      key.lstrip('_'): val
      for (key, val) in self.__dict__.items()
    }