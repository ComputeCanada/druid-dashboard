# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
from manager.template import _resolve, Template

# ---------------------------------------------------------------------------
#                                                               __resolve()
# ---------------------------------------------------------------------------

def test_resolve_empty_dict():
  """
  Test that resolving variables in an empty dict returns "undefined" as value
  but does not raise an exception or otherwise fail.
  """
  d = {}

  assert _resolve(d, 'foo') is None
  assert _resolve(d, 'foo.bar') is None

def test_resolve():
  """
  Test that querying variables in a populated dict works as expected:
  - simple 1-deep variables are returned
  - simple N-deep variables are returned
  - missing 1-deep variables are handled gracefully
  - missing N-deep variables are handled gracefully
  - complex variables are returned
  """
  d = {
    'foo': 'bar',
    'ding': {
      'dang': 'doo',
      'dong': 'bell'
    },
    'thing': 'thong'
  }

  assert _resolve(d, 'foo') == 'bar'
  assert _resolve(d, 'ding.dang') == 'doo'
  assert _resolve(d, 'bleep') is None
  assert _resolve(d, 'raz.ma') is None
  assert _resolve(d, 'ding') == {'dang': 'doo', 'dong': 'bell'}

# ---------------------------------------------------------------------------
#                                                            Template class
# ---------------------------------------------------------------------------

def test_template():
  """
  Test that template content renders correctly.
  """
  content = '''
Dear {user}:

This is a test template.  You've requested {summary.cpu} CPUs, {summary.mem}
memory and {summary.nodes} nodes in a job.  This will never run.

Also this value should be undefined: {not.a.variable}

Sincerely,
{analyst}
'''
  values = {
    'user': 'Tracy',
    'summary': {
      'cpu': 32,
      'mem': '250G',
      'nodes': 1024
    },
    'analyst': 'Chris'
  }
  template = Template(content=content)
  text = template.render(values=values)
  print(text)
  assert text == '''
Dear Tracy:

This is a test template.  You've requested 32 CPUs, 250G
memory and 1024 nodes in a job.  This will never run.

Also this value should be undefined: [undefined]

Sincerely,
Chris
'''
