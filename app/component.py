# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=W0621
#
from datetime import date
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

SQL_GET_BY_CLUSTER_AND_SERVICE = '''
  SELECT  id, name
  FROM    components
  WHERE   cluster = ? AND service = ?
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

  def __init__(self, id=None, name=None, cluster=None, service=None, get_last_heard=False, factory_load=False):

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
    elif not id and not name and cluster and service:
      res = db.execute(SQL_GET_BY_CLUSTER_AND_SERVICE, (cluster, service)).fetchone()
      if res:
        self._id = res['id']
        self._name = res['name']
        if get_last_heard:
          self.load_lastheard()
      else:
        raise ValueError(
          "Could not load component for cluster {} and service {}".format(
            cluster, service
          ))
    elif not cluster and not service:
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
    elif id and name and cluster and service:
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
    else:
      # TODO: this exception is a pile of worms in a police uniform
      raise Exception("Bad call: specify, id, id and name, cluster and service, or everything")

  def load_lastheard(self):
    # query related API keys for most recently used
    self._lastheard = most_recent_use(self._id)

  @property
  def lastheard(self):
    if not self._lastheard:
      self.load_lastheard()
    return self._lastheard

  @property
  def cluster(self):
    return self._cluster

  def serializable(self):
    tmp = {
      key.lstrip('_'): val
      for (key, val) in self.__dict__.items()
    }

    # Postgres/Psycopg use date object for timestamps, whereas SQLite uses
    # strings.  The string SQLite returns includes microseconds; the default
    # string representation of the date object does not.  Which would generally
    # be okay except it causes tests verifying lastheard was updated to fail
    # unless a one-second sleep is introduced.
    if self._lastheard and isinstance(self._lastheard, date):
      tmp['lastheard'] = self._lastheard.isoformat()

    return tmp
