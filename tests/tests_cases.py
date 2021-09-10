# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
import json
import pytest
from manager.exceptions import AppException, BadCall
from manager.case import just_job_id, dict_to_table, json_to_table, CaseRegistry, Case

# ---------------------------------------------------------------------------
#                                                          just_job_id()
# ---------------------------------------------------------------------------

def test_just_job_id_int_only():
  """
  Tests a basic job ID like (int) 423.
  """
  assert just_job_id(423) == 423

def test_just_job_id_int_string():
  """
  Tests a basic job ID like "423".
  """
  assert just_job_id("423") == 423

def test_just_job_id_array():
  """
  Tests a job ID that is part of an array.
  """
  assert just_job_id("423_32") == 423

def test_just_job_id_bad_pattern():
  """
  Tests a malformed job ID causes an exception to be raised.
  """
  with pytest.raises(AppException) as e:
    just_job_id("_32")
  assert str(e.value) == "Could not parse job ID ('_32') to extract base ID"

# ---------------------------------------------------------------------------
#                                                          dict_to_table()
# ---------------------------------------------------------------------------

def test_dict_to_table_no_dict():
  assert dict_to_table(None) == ''

def test_dict_to_table_empty_dict():
  assert dict_to_table({}) == ''

def test_dict_to_table_flat_dict():
  d = {
    'k1': 'v1',
    'k2': 'v2',
    'k3': 'v3'
  }
  assert dict_to_table(d) == '<table><tr><th>k1</th><td>v1</td></tr>' \
    '<tr><th>k2</th><td>v2</td></tr><tr><th>k3</th><td>v3</td></tr></table>'

def test_dict_to_table_complex_dict():
  d = {
    'k1': 'v1',
    'k2': {
      'k2a': 'v2a',
      'k2b': 'v2b'
    }
  }
  print(dict_to_table(d))
  assert dict_to_table(d) == "<table><tr><th>k1</th><td>v1</td></tr>" \
    "<tr><th>k2</th><td>{'k2a': 'v2a', 'k2b': 'v2b'}</td></tr></table>"

# ---------------------------------------------------------------------------
#                                                          json_to_table()
# ---------------------------------------------------------------------------

def test_json_to_table_no_dict():
  assert json_to_table('null') == ''

def test_json_to_table_empty_dict():
  assert json_to_table('{}') == ''

def test_json_to_table_flat_dict():
  d = {
    'k1': 'v1',
    'k2': 'v2',
    'k3': 'v3'
  }
  j = json.dumps(d)
  assert json_to_table(j) == '<table><tr><th>k1</th><td>v1</td></tr>' \
    '<tr><th>k2</th><td>v2</td></tr><tr><th>k3</th><td>v3</td></tr></table>'

def test_json_to_table_complex_dict():
  d = {
    'k1': 'v1',
    'k2': {
      'k2a': 'v2a',
      'k2b': 'v2b'
    }
  }
  j = json.dumps(d)
  assert json_to_table(j) == "<table><tr><th>k1</th><td>v1</td></tr>" \
    "<tr><th>k2</th><td>{'k2a': 'v2a', 'k2b': 'v2b'}</td></tr></table>"

# ---------------------------------------------------------------------------
#                                                             CaseRegistry
# ---------------------------------------------------------------------------

# pylint: disable=abstract-method
class FakeCase(Case):
  pass

# pylint: disable=abstract-method
class RealizedCase(Case):
  @classmethod
  def describe_me(cls):
    return {
      'cols': []
    }

def test_get_registry():
  registry = CaseRegistry.get_registry()
  assert registry is not None

# pylint: disable=unused-variable
def test_get_registry_myself():
  with pytest.raises(BadCall) as e:
    registry = CaseRegistry()
  assert str(e.value) == "Cannot create two instances of this class.  Use get_registry()"

def test_register_garbage_reporter():
  registry = CaseRegistry.get_registry()
  with pytest.raises(AppException) as e:
    registry.register('fakereporter', None)
  assert str(e.value) == "The reporter is not a subclass of Case"

def test_register_garbage_reporter_II():
  registry = CaseRegistry.get_registry()
  with pytest.raises(AppException) as e:
    registry.register('fakereporter', object)
  assert str(e.value) == "The reporter is not a subclass of Case"

def test_register_unrealized_reporter():
  """
  When a Case subclass is registered but does not implement the describe_me()
  function, an exception is thrown.
  """
  registry = CaseRegistry.get_registry()
  with pytest.raises(NotImplementedError):
    registry.register('fakereporter', FakeCase)

def test_register_reporter():
  registry = CaseRegistry.get_registry()
  registry.register('reporter', RealizedCase)

def test_register_reporter_duplicate():
  registry = CaseRegistry.get_registry()
  with pytest.raises(AppException) as e:
    registry.register('reporter', RealizedCase)
  assert str(e.value) == "A reporter has already been registered with that name: reporter"

def test_registry_get_reporters():
  registry = CaseRegistry.get_registry()
  print(registry.reporters)
  assert registry.reporters.get('reporter', None) == RealizedCase

def test_registry_get_descriptions():
  registry = CaseRegistry.get_registry()
  assert registry.descriptions is not None

def test_registry_deregister():
  registry = CaseRegistry.get_registry()
  registry.deregister('reporter')
  assert registry.reporters.get('reporter', None) is None
  assert registry.descriptions.get('reporter', None) is None

def test_registry_deregister_unknown():
  """
  We don't care about nonsense reporters, and that's all deregistering is
  really for, so this passes so long as it doesn't throw errors--there's
  nothing to check.
  """
  registry = CaseRegistry.get_registry()
  registry.deregister('reporter')
