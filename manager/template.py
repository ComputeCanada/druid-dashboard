# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
import re
from flask_babel import _
from manager.db import get_db
from manager.log import get_log
from manager.exceptions import ResourceNotFound, BadCall

# regular expression for substituting template variables
_re = r'{(?P<var>\w[.\w]*)}'
_rec = re.compile(_re)

# ---------------------------------------------------------------------------
#                                                               SQL queries
# ---------------------------------------------------------------------------

SQL_GET = '''
  SELECT  content
  FROM    templates
  WHERE   name = ?
  AND     language = ?
'''

# ---------------------------------------------------------------------------
#                                                                   Helpers
# ---------------------------------------------------------------------------

def _resolve(dikt, var):
  """
  Resolve a complex key using dot notation to a value in a dict.

  Args:
    dikt: Dictionary of key-value pairs, where some values may be sub
      dictionaries, recursively.
    var: Key or string of dot-separated keys denoting path through dict

  Returns:
    The referenced value, or None if none found
  """
  arr = var.split('.', 1)
  try:
    if len(arr) == 1:
      return dikt[arr[0]]
    return _resolve(dikt[arr[0]], arr[1])
  except KeyError:
    return None

# ---------------------------------------------------------------------------
#                                                            Template class
# ---------------------------------------------------------------------------

class Template:

  def __init__(self, name=None, language=None, content=None):
    """
    Initialize template object.

    Args:
      name: name of template in database
      language: language to use
      content: template content

    Notes:
      Either name or content must be specified.
    """
    if name:
      res = get_db().execute(SQL_GET, (name, language or '')).fetchone()
      if not res:
        error = "Could not load requested template (name=%s, language=%s) from database" % \
          (name, language)
        get_log().error(error)
        raise ResourceNotFound(error)
      self._content = res['content']
    elif content:
      self._content = content
    else:
      raise BadCall('Must specify either template name or content')

  def render(self, values=None):
    values = values or {}
    return re.sub(
      _rec,
      lambda x: str(_resolve(values, x['var']) or _("[undefined]")),
      self._content
    )
