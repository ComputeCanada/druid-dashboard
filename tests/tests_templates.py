# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
from manager.template import __resolve

# ---------------------------------------------------------------------------
#                                                          __resolve()
# ---------------------------------------------------------------------------

def test_resolve_empty_dict():
  """
  Test that resolving variables in an empty dict returns "undefined" as value
  but does not raise an exception or otherwise fail.
  """
  d = {}

  assert __resolve(d, 'foo') is None
  assert __resolve(d, 'foo.bar') is None

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

  assert __resolve(d, 'foo') == 'bar'
  assert __resolve(d, 'ding.dang') == 'doo'
  assert __resolve(d, 'bleep') is None
  assert __resolve(d, 'raz.ma') is None
  assert __resolve(d, 'ding') == {'dang': 'doo', 'dong': 'bell'}
