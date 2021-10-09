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

# select pi_only, label, title  from templates t JOIN templates_content tc ON
# name = template where name='candidate' and language='en';
SQL_GET = '''
  SELECT  pi_only, label, title, body
  FROM    templates
  JOIN    templates_content
  ON      name = template
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

def _render(content, values):
  # trivial case, but retain empty string or None as given
  if not content:
    return content
  return re.sub(
    _rec,
    lambda x: str(_resolve(values, x['var']) or _("[undefined]")),
    content
  )

# ---------------------------------------------------------------------------
#                                                            Template class
# ---------------------------------------------------------------------------

class Template:

  def __init__(self,
      name=None, language=None,
      label=None, title=None, body=None
    ):
    """
    Initialize template object in a persistent or ephemeral context.

    Args:
      name: name of template in database
      language: language to use
      label: display name of this template in given language
      title: title for template body, ex. e-mail subject
      body: template body

    Notes:
      Either name or body must be specified.  If only name is specified, the
      template is loaded from the database using the name and language as
      keys.  If only body is specified, then a non-persisting template is
      created (this is used in unit testing and may not have other uses).  If
      the name and body are specified, a new template object is created to be
      persisted for future use.
    """
    if name and not body:
      # retrieve template record
      res = get_db().execute(SQL_GET, (name, language or '')).fetchone()
      if not res:
        error = "Could not load requested template (name=%s, language=%s) from database" % \
          (name, language)
        get_log().error(error)
        raise ResourceNotFound(error)
      self._name = name
      self._label = res['label']
      self._title = res['title']
      self._body = res['body']
    elif body:
      self._title = title
      self._body = body
      if name:
        self._name = name
        self._label = label or name

        # create persistent template record
        # TODO
    else:
      raise BadCall('Must specify either template name or content')

  def render(self, values=None):
    values = values or {}
    self._title_rendered = _render(self._title, values)
    self._body_rendered = _render(self._body, values)

  @property
  def title(self):
    return self._title_rendered

  @property
  def body(self):
    return self._body_rendered

  # TODO: add to Seralizable class and inherit?
  def serialize(self):
    dikt = {
      key.lstrip('_'): val
      for (key, val) in self.__dict__.items()
    }
    return dikt
