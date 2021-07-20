# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
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
      'actions': None,
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
          'resource': 'cpu',
          'resource_pretty': 'CPU',
          'state': 'rejected',
          'state_pretty': 'Rejected',
          'submitters': ['userQ'],
          'summary': {},
          'ticket': None,
          'ticket_id': None,
          'ticket_no': None,
          'ticks': 4
        },
        {
          'account': 'def-bobaloo-aa',
          'claimant': None,
          'cluster': 'testcluster',
          'id': 3,
          'jobrange': [1015, 2015],
          'other': {'notes': 0},
          'pain': 1.5,
          'resource': 'cpu',
          'resource_pretty': 'CPU',
          'state': 'pending',
          'state_pretty': 'Pending',
          'submitters': ['userQ', 'userX'],
          'summary': {},
          'ticket': None,
          'ticket_id': None,
          'ticket_no': None,
          'ticks': 3
        }
      ]
    },
  }

def test_update_case_xhr(client):
  data = [
    {
      'note': 'Reverting to <b>pending</b>',
      'datum': 'state',
      'value': 'pending',
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
      'actions': None,
      'results': [
        {
          'account': 'def-dleske-aa',
          'claimant': 'tst-003',
          'claimant_pretty': 'User 1',
          'cluster': 'testcluster',
          'id': 2,
          'jobrange': [1005, 3000],
          'other': {'notes': 4},
          'pain': 1.0,
          'resource': 'cpu',
          'resource_pretty': 'CPU',
          "state":"pending",
          "state_pretty": "Pending",
          'submitters': ['userQ'],
          'summary': {},
          'ticket': None,
          'ticket_id': None,
          'ticket_no': None,
          'ticks': 4
        },
        {
          'account': 'def-bobaloo-aa',
          'claimant': None,
          'cluster': 'testcluster',
          'id': 3,
          'jobrange': [1015, 2015],
          'other': {'notes': 0},
          'pain': 1.5,
          'resource': 'cpu',
          'resource_pretty': 'CPU',
          'state': 'pending',
          'state_pretty': 'Pending',
          'submitters': ['userQ', 'userX'],
          'summary': {},
          'ticket': None,
          'ticket_id': None,
          'ticket_no': None,
          'ticks': 3
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
      'datum': 'state',
      'was': 'p',
      'now': 'r',
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
      'datum': None,
      'was': None,
      'now': None
    },
    {
      'id': 2,
      'caseID': 2,
      'analyst': 'tst-003',
      'analyst_pretty': 'User 1',
      'text': 'This is not the way',
      'datum': 'claimant',
      'was': None,
      'now': 'tst-003',
      'type': 'History'
    },
    {
      'id': 3,
      'caseID': 2,
      'analyst': 'tst-003',
      'analyst_pretty': 'User 1',
      'text': 'Reverting to &lt;b&gt;pending&lt;/b&gt;',
      'datum': 'state',
      'was': 'r',
      'now': 'p',
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

  print(x)
  assert x == []

def test_update_cases_xhr_no_timestamps(client):
  data = [
    {
      'note': 'Stupid note',
      'datum': 'state',
      'value': 'rejected',
    },
    {
      'note': 'Reverting to pending again',
      'datum': 'state',
      'value': 'pending',
    },
    {
      'note': 'This is not the way of the leaf',
      'datum': 'claimant',
      'value': 'tst-003',
    },
    {
      'note': 'I just do not ascertain this chap',
    },
  ]
  response = client.patch('/xhr/cases/3', json=data, environ_base={'HTTP_X_AUTHENTICATED_USER': 'user1'})
  print(response.data)
  assert response.status_code == 200
