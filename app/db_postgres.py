# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
import psycopg2
import psycopg2.extensions


def register_adapter(target):
  psycopg2.extensions.register_adapter(target, target)


class DictCursor(psycopg2.extensions.cursor):
  """
  Custom cursor factory to provide name-subscriptable fields, similar to that
  provided by SQLite3 by default.  It may be slightly more efficient to use
  numerical subscripts, but this is self-documenting in the code.
  """

  def fetchone(self):
    tup = super().fetchone()
    if tup:
      return {self.description[x].name: tup[x] for x in range(0, len(tup))}
    return None

  def fetchall(self):
    tup = super().fetchall()
    if tup:
      numcols = len(tup[0])
      numrows = len(tup)
      return [
        {
          self.description[y].name: tup[x][y] for y in range(0, numcols)
        } for x in range(0, numrows)
      ]
    return None

class ExtConnection(psycopg2.extensions.connection):
  """
  Custom connection class which reports its type and provides shortcuts to
  query execution methods provided in the cursor object, in order to normalize
  to what is provided by SQLite3.
  """

  type = 'postgres'

  def execute(self, sql, parameters=None):
    cursor = self.cursor()
    cursor.execute(sql.replace('?', '%s'), parameters)
    return cursor

  def executemany(self, sql, seq):
    cursor = self.cursor()
    cursor.executemany(sql.replace('?', '%s'), seq)
    return cursor

  def executescript(self, sql):
    cursor = self.cursor()
    cursor.execute(sql)
    return cursor


def open_db_postgres(uri):
  db = psycopg2.connect(uri,
                        connection_factory=ExtConnection,
                        cursor_factory=DictCursor)
  return db
