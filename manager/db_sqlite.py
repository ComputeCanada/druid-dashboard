# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
from enum import Enum
import re
import sqlite3
from manager.exceptions import DatabaseException


def register_adapter(target):
  sqlite3.register_adapter(target, target.__str__)


def iter_flatten(iterable):
  """
  Iterator for flattening a list or tuple.  Can be nested.

  From http://rightfootin.blogspot.com/2006/09/more-on-python-flatten.html
  """
  it = iter(iterable)
  for e in it:
    if isinstance(e, (list, tuple)):
      for f in iter_flatten(e):
        yield f
    else:
      yield e

def flatten(t):
  """
  Flatten a list or tuple and return a flat list.
  """
  return list(iter_flatten(t))

def nextqparm(sql):
  """
  This generator tokenizes an SQL query string into static tokens--essentially
  anything not a query parameter placeholder ("?").  This generator yields the
  current non-placeholder token when either a placeholder occurs, or at the end
  of the query string.  It is left to the caller to know (based on its
  parameter list) when iteration is done.
  """

  # RE for tokenizing query strings into everything not '?' token
  regex = re.compile("((?:[^?']*(?:'[^']*')?)*)")

  # iterate through regular expression matches
  everythingelse = ''
  for m in regex.finditer(sql):

    # hit a query parameter placeholder?
    if m.groups()[0] == '':

      # give up the other stuff gathered so far and then clear it on return
      yield everythingelse
      everythingelse = ''

    else:
      everythingelse += m.groups()[0]

  # nothing left to iterate, give up anything leftover before returning
  if everythingelse != '':
    yield everythingelse

class ExtConnection(sqlite3.Connection):
  """
  The SQLite3 connection object is subclassed to normalize it with the Postgres
  connection class (and vice-versa).  The execute() method is overridden to
  interpret query placeholders for list or tuple parameters.  As well, some
  syntactical sugar is introduced.
  """

  # convenience for enabling other code to make decisions based on DB type
  type = 'sqlite'

  def execute(self, sql, parameters=None):
    """
    Extend sqlite3.Connection.execute() in order to handle lists and tuples
    as query parameters.
    """

    if parameters:
      newsql = ''

      # iterator breaks query string down into static tokens: points of
      # separation indicate query parameters
      qparms = nextqparm(sql)

      # consume static tokens between query parameters
      converted = []
      for p in parameters:
        newsql += next(qparms)
        if isinstance(p, (list, tuple)):
          newsql += ','.join(['?'] * len(p))
        else:
          newsql += '?'

        # also check if this is a Enum
        if issubclass(type(p), Enum):
          converted.append(p.value)
        else:
          converted.append(p)

      # use up remaining string tokens
      if __debug__:
        # there should only be one; check this in test runs
        gotone = False
      for tok in qparms:
        if __debug__:
          if gotone:
            raise DatabaseException("SQLite: Should not have any more qparms in token parsing")
          gotone = True
        newsql += tok

      return sqlite3.Connection.execute(self, newsql, flatten(converted))

    return sqlite3.Connection.execute(self, sql)

def open_db_sqlite(uri):
  """
  Open SQLite database connection.  Uses internal subclass of SQLite3's
  Connection class with a few extras.

  In order to be able to use SQLite3 and Postgres interchangeably (SQLite3 for
  most of the development and quick testing, Postgres for most of the
  integration testing and all production) there has been some effort into
  normalizing slight differences between the two implementations of Python's
  DB-API v2.

  For SQLite: support the use of lists or tuples in query parameters.
  """

  db = ExtConnection(uri, uri=True)
  db.row_factory = sqlite3.Row

  return db
