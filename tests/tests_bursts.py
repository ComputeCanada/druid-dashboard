# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=line-too-long
#
import json

# ---------------------------------------------------------------------------
#                                                                      ajax
# ---------------------------------------------------------------------------

def test_get_cases_xhr(client):
  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'user1'})
  assert response.status_code == 200

  response = client.get('/xhr/cases/?cluster=testcluster')
  assert response.status_code == 200
  interpreted = json.loads(response.data.decode('utf-8'))

  # assert basic structure of response
  assert interpreted['cluster'] == 'testcluster'
  assert interpreted['bursts']
  assert interpreted['bursts']['results'][0]['epoch'] == interpreted['bursts']['epoch']

  # take care of test-to-test variance
  del interpreted['bursts']['results'][0]['epoch']
  del interpreted['bursts']['results'][1]['epoch']
  del interpreted['bursts']['epoch']
  interpreted['bursts']['results'][1]['submitters'].sort()

  print(interpreted)
  assert interpreted == {
    'cluster': 'testcluster',
    'bursts': {
      'results': [
        {
          'account': 'def-dleske-aa',
          'claimant': 'tst-003',
          'claimant_pretty': 'User 1',
          'cluster': 'testcluster',
          'id': 2,
          'jobrange': [1005, 3000],
          'other': {'notes': 2},
          'pain': 1.0,
          'pain_pretty': '1.00',
          'resource': 'cpu',
          'resource_pretty': 'CPU',
          'state': 'rejected',
          'state_pretty': 'Rejected',
          'submitters': ['userQ'],
          'summary': None,
          'ticket': None,
          'ticket_id': None,
          'ticket_no': None,
          'ticks': 4,
          'usage_pretty': '<a target="beamplot" href="https://localhost/plots/testcluster/def-dleske-aa_cpu_cumulative.html">Cumulative</a>\n    <br/>\n    <a target="beamplot" href="https://localhost/plots/testcluster/def-dleske-aa_cpu_instant.html">Instant</a>'
        },
        {
          'account': 'def-bobaloo-aa',
          'actions': [{'id': 'reject', 'label': 'Reject'}],
          'claimant': None,
          'cluster': 'testcluster',
          'id': 3,
          'jobrange': [1015, 2015],
          'other': {'notes': 0},
          'pain': 1.5,
          'pain_pretty': '1.50',
          'resource': 'cpu',
          'resource_pretty': 'CPU',
          'state': 'pending',
          'state_pretty': 'Pending',
          'submitters': ['userQ', 'userX'],
          'summary': None,
          'ticket': None,
          'ticket_id': None,
          'ticket_no': None,
          'ticks': 3,
          'usage_pretty': '<a target="beamplot" href="https://localhost/plots/testcluster/def-bobaloo-aa_cpu_cumulative.html">Cumulative</a>\n    <br/>\n    <a target="beamplot" href="https://localhost/plots/testcluster/def-bobaloo-aa_cpu_instant.html">Instant</a>'
        }
      ]
    },
  }

def test_get_case_xhr(client):
  """
  Test that we get expected info about a case.
  """
  response = client.get('/xhr/cases/2', environ_base={'HTTP_X_AUTHENTICATED_USER': 'user1'})
  print(response.data)
  d = json.loads(response.data.decode())
  assert 'account' in d
  assert 'resource' in d
  assert 'templates' in d
  assert 'users' in d
  assert response.status_code == 200

def test_get_unknown_case_xhr(client):
  """
  Test that we get a reasonable error when requesting information about a
  nonexistent case.
  """
  # TODO: the following gets an HTML response instead of a JSON one
  #response = client.get('/xhr/cases/4')

  response = client.get('/xhr/cases/4', environ_base={'HTTP_X_AUTHENTICATED_USER': 'user1'})
  print(response.data)
  assert response.status_code == 404

def test_update_case_xhr(client):
  data = [
    {
      'note': 'Reverting to <b>pending</b>',
      'state': 'pending',
      'timestamp':'2019-03-31 10:37 AM'
    },
    {
      'note': 'I just dinnae aboot this guy',
      'timestamp':'2019-03-31 10:32 AM'
    },
  ]
  response = client.patch('/xhr/cases/2', json=data, environ_base={'HTTP_X_AUTHENTICATED_USER': 'user1'})
  print(response.data)
  assert response.status_code == 200
  interpreted = json.loads(response.data.decode('utf-8'))

  # take care of test-to-test variance
  del interpreted['bursts']['results'][0]['epoch']
  del interpreted['bursts']['results'][1]['epoch']
  del interpreted['bursts']['epoch']
  interpreted['bursts']['results'][1]['submitters'].sort()
  print(interpreted)
  assert interpreted == {
    'cluster': 'testcluster',
    'bursts': {
      'results': [
        {
          'account': 'def-dleske-aa',
          'actions': [{'id': 'reject', 'label': 'Reject'}],
          'claimant': 'tst-003',
          'claimant_pretty': 'User 1',
          'cluster': 'testcluster',
          'id': 2,
          'jobrange': [1005, 3000],
          'other': {'notes': 4},
          'pain': 1.0,
          'pain_pretty': '1.00',
          'resource': 'cpu',
          'resource_pretty': 'CPU',
          "state":"pending",
          "state_pretty": "Pending",
          'submitters': ['userQ'],
          'summary': None,
          'ticket': None,
          'ticket_id': None,
          'ticket_no': None,
          'ticks': 4,
          'usage_pretty': '<a target="beamplot" href="https://localhost/plots/testcluster/def-dleske-aa_cpu_cumulative.html">Cumulative</a>\n    <br/>\n    <a target="beamplot" href="https://localhost/plots/testcluster/def-dleske-aa_cpu_instant.html">Instant</a>'
        },
        {
          'account': 'def-bobaloo-aa',
          'actions': [{'id': 'reject', 'label': 'Reject'}],
          'claimant': None,
          'cluster': 'testcluster',
          'id': 3,
          'jobrange': [1015, 2015],
          'other': {'notes': 0},
          'pain': 1.5,
          'pain_pretty': '1.50',
          'resource': 'cpu',
          'resource_pretty': 'CPU',
          'state': 'pending',
          'state_pretty': 'Pending',
          'submitters': ['userQ', 'userX'],
          'summary': None,
          'ticket': None,
          'ticket_id': None,
          'ticket_no': None,
          'ticks': 3,
          'usage_pretty': '<a target="beamplot" href="https://localhost/plots/testcluster/def-bobaloo-aa_cpu_cumulative.html">Cumulative</a>\n    <br/>\n    <a target="beamplot" href="https://localhost/plots/testcluster/def-bobaloo-aa_cpu_instant.html">Instant</a>'
        }
      ]
    },
  }

def test_get_events(client):
  """
  Get events related to a case.
  """
  # log in
  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'user1'})
  assert response.status_code == 200

  # get events
  response = client.get('/xhr/cases/2/events/')
  assert response.status_code == 200
  x = json.loads(response.data)

  # we don't really need to delete IDs but we do need to delete timestamps
  # because SQLite and Postgres report them differently
  del x[0]['timestamp']
  del x[1]['timestamp']
  del x[2]['timestamp']
  del x[3]['timestamp']
  print(x)
  assert x == [
    {
      'id': 1,
      'caseID': 2,
      'analyst': 'tst-003',
      'analyst_pretty': 'User 1',
      'change': {
        'datum': 'state',
        'was': 'pending',
        'now': 'rejected'
      },
      'text': 'Hey how are ya',
      'type': 'History'
    },
    {
      'id': 4,
      'caseID': 2,
      'analyst': 'tst-003',
      'analyst_pretty': 'User 1',
      'text': 'I just dinnae aboot this guy',
      'type': 'History',
      'change': None
    },
    {
      'id': 2,
      'caseID': 2,
      'analyst': 'tst-003',
      'analyst_pretty': 'User 1',
      'text': 'This is not the way',
      'change': {
        'datum': 'claimant',
        'was': None,
        'now': 'tst-003'
      },
      'type': 'History'
    },
    {
      'id': 3,
      'caseID': 2,
      'analyst': 'tst-003',
      'analyst_pretty': 'User 1',
      'text': 'Reverting to &lt;b&gt;pending&lt;/b&gt;',
      'change': {
        'datum': 'state',
        'was': 'rejected',
        'now': 'pending'
      },
      'type': 'History'
    },
  ]

def test_get_no_events(client):
  """
  Get events related to a burst when there are no events.
  """
  # log in
  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'user1'})
  assert response.status_code == 200

  # get events
  response = client.get('/xhr/cases/1/events/')
  print(response)
  assert response.status_code == 200
  x = json.loads(response.data)
  assert x is None

def test_update_cases_xhr_no_timestamps(client):
  data = [
    {
      'note': 'Stupid note',
      'state': 'rejected',
    },
    {
      'note': 'Reverting to pending again',
      'state': 'pending',
    },
    {
      'note': 'This is not the way of the leaf',
      'claimant': 'tst-003',
    },
    {
      'note': 'I just do not ascertain this chap',
    },
  ]
  response = client.patch('/xhr/cases/3', json=data, environ_base={'HTTP_X_AUTHENTICATED_USER': 'user1'})
  print(response.data)
  assert response.status_code == 200
