# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
import re
from manager.db import get_db
from manager.log import get_log
from manager.exceptions import ResourceNotFound

# regular expression for substituting template variables
_re = r'%(?P<var>\w+)%'
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
#                                                            Template class
# ---------------------------------------------------------------------------

class Template:

  def __init__(self, name, language=''):
    res = get_db().execute(SQL_GET, (name, language)).fetchone()
    if not res:
      error = "Could not load requested template (name=%s, language=%s) from database" % \
        (name, language)
      get_log().error(error)
      raise ResourceNotFound(error)
    self._content = res['content']

  def render(self, values=None):
    values = values or {}
    return re.sub(
      _rec,
      lambda x: str(values.get(x['var'], "[undefined]")),
      self._content
    )
