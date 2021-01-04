# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=W0621
#
from app.db import get_db
from app.exceptions import DatabaseException

# ---------------------------------------------------------------------------
#                                                               SQL queries
# ---------------------------------------------------------------------------

SQL_GET = '''
  SELECT    name, cluster, service
  FROM      components
  WHERE     id = ?
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

SQL_UPDATE_LASTHEARD = '''
  UPDATE components
  SET     lastheard = ?
  WHERE   id = ?
'''

SQL_UPDATE_NAME = '''
  UPDATE  components
  SET     name = ?
  WHERE   id = ?
'''

# ---------------------------------------------------------------------------
#                                                                   helpers
# ---------------------------------------------------------------------------


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

  def __init__(self, id, name=None, cluster=None, service=None):

    self._id = id
    self._name = name
    self._cluster = cluster
    self._service = service
    self._lastheard = None

    # creating or retrieving?
    db = get_db()
    if id and not name:
      res = db.execute(SQL_GET, (id,)).fetchone()
      if res:
        self._name = res['name']
        self._cluster = res['cluster']
        self._service = res['service']
        self._lastheard = res['lastheard']
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
          "id='{}', name='{}', cluster='{}', service='{}'".format(
            id, name, cluster, service
          )
        ) from e

  def commit(self):
    # for now only used for updating lastheard field
    if self._lastheard:
      db = get_db()
      try:
        db.execute(SQL_UPDATE_LASTHEARD, (self._lastheard, self._id))
        db.commit()
      except Exception as e:
        raise DatabaseException(
          "Could not execute SQL_UPDATE_LASTHEARD for component {}".format(id)
        ) from e

  @property
  def lastheard(self):
    return self._lastheard

  @lastheard.setter
  def lastheard(self, value):
    self._lastheard = value
    self.commit()
