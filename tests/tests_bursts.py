# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
import json

# ---------------------------------------------------------------------------
#                                                                      ajax
# ---------------------------------------------------------------------------

def test_get_bursts_xhr(client):
  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'user1'})
  assert response.status_code == 200

  response = client.get('/xhr/bursts/')
  assert response.status_code == 200
  interpreted = json.loads(response.data.decode('utf-8'))
  assert interpreted['testcluster']['bursts'][0]['epoch'] == interpreted['testcluster']['epoch']
  del interpreted['testcluster']['bursts'][0]['epoch']
  del interpreted['testcluster']['bursts'][1]['epoch']
  del interpreted['testcluster']['epoch']
  print(interpreted)
  assert interpreted == {
    "testcluster": {
      "bursts": [
        {"account":"def-dleske-aa","claimant":'tst-003',"cluster":"testcluster",
          "id":13,"jobrange":[1005,3000],"pain":1.0, "state":"rejected",
          "state_pretty":"Rejected","summary":"{}","ticks":3,"resource":"cpu",
          "resource_pretty":"CPU","ticket_id":None, "ticket_no":None,
          "ticket_href":None,"submitters":["userQ"], 'other': {'notes': 0},
          'claimant_pretty':'User 1'},
        {'account': 'def-bobaloo-aa', 'claimant': None, 'cluster':
          'testcluster', 'id': 14, 'jobrange': [1015, 2015],
          'other': {'notes': 0}, 'pain': 1.5, 'resource': 'cpu', 'resource_pretty':
          'CPU', 'state': 'pending', 'state_pretty': 'Pending', 'submitters': ['userQ', 'userX'],
          'summary': '{}', 'ticket_href': None, 'ticket_id': None, 'ticket_no': None,
          'ticks': 2}
      ],
    },
    "testcluster2": {
      "bursts": [
        {"account":"def-aaa-aa","claimant":None,"cluster":"testcluster2",
          "epoch":25,"id":9,"jobrange":[15,25],"pain":2.5,"state":"pending",
          "state_pretty":"Pending","summary":None,"ticks":0,"resource":"cpu",
          "resource_pretty":"CPU","ticket_id":None, "ticket_no":None,
          "ticket_href":None,"submitters":["userQ"], 'other': {'notes': 0}},
        {"account":"def-bbb-aa","claimant":None,"cluster":"testcluster2",
          "epoch":25,"id":10,"jobrange":[16,26],"pain":2.5,"state":"pending",
          "state_pretty":"Pending","summary":None,"ticks":0,"resource":"cpu",
          "resource_pretty":"CPU","ticket_id":None, "ticket_no":None,
          "ticket_href":None,"submitters":["userQ"], 'other': {'notes': 0}},
        {"account":"def-ccc-aa","claimant":None,"cluster":"testcluster2",
          "epoch":25,"id":11,"jobrange":[17,27],"pain":2.5,"state":"pending",
          "state_pretty":"Pending","summary":None,"ticks":0,"resource":"cpu",
          "resource_pretty":"CPU","ticket_id":None, "ticket_no":None,
          "ticket_href":None,"submitters":["userQ"], 'other': {'notes': 0}}
      ],
      "epoch":25
    }
  }


def test_update_bursts_xhr(client):
  data = [
    {
      'id':13,
      'note': 'Reverting to <b>pending</b>',
      'state': 'pending',
      'timestamp':'2019-03-31 10:37 AM'
    },
    {
      'id': 13,
      'note': 'I just dinnae aboot this guy',
      'timestamp':'2019-03-31 10:32 AM'
    },
  ]
  response = client.patch('/xhr/bursts/', json=data, environ_base={'HTTP_X_AUTHENTICATED_USER': 'user1'})
  print(response.data)
  assert response.status_code == 200
  interpreted = json.loads(response.data.decode('utf-8'))
  del interpreted['testcluster']['bursts'][0]['epoch']
  del interpreted['testcluster']['bursts'][1]['epoch']
  del interpreted['testcluster']['epoch']
  print(interpreted)
  assert interpreted == {
    "testcluster": {
      "bursts": [
        {
          "account":"def-dleske-aa",
          "claimant":'tst-003',
          "claimant_pretty":'User 1',
          "cluster":"testcluster",
          "resource":"cpu",
          "resource_pretty": "CPU",
          "id":13,
          "jobrange":[1005,3000],
          "submitters":["userQ"],
          "pain":1.0,
          "state":"pending",
          "state_pretty": "Pending",
          "summary": "{}",
          "ticket_id": None,
          "ticket_no": None,
          "ticket_href":None,
          "ticks": 3,
          'other': {'notes': 1}
        },
        {'account': 'def-bobaloo-aa', 'claimant': None, 'cluster':
          'testcluster', 'id': 14, 'jobrange': [1015, 2015],
          'other': {'notes': 0}, 'pain': 1.5, 'resource': 'cpu', 'resource_pretty':
          'CPU', 'state': 'pending', 'state_pretty': 'Pending', 'submitters': ['userQ', 'userX'],
          'summary': '{}', 'ticket_href': None, 'ticket_id': None, 'ticket_no': None,
          'ticks': 2}
      ],
    },
    "testcluster2": {
      "bursts": [
        {"account":"def-aaa-aa","claimant":None,"cluster":"testcluster2",
          "epoch":25,"id":9,"jobrange":[15,25],"pain":2.5,"state":"pending",
          "state_pretty":"Pending","summary":None,"ticks":0,"resource":"cpu",
          "resource_pretty":"CPU","ticket_id":None, "ticket_no":None,
          "ticket_href":None,"submitters":["userQ"], 'other': {'notes': 0}},
        {"account":"def-bbb-aa","claimant":None,"cluster":"testcluster2",
          "epoch":25,"id":10,"jobrange":[16,26],"pain":2.5,"state":"pending",
          "state_pretty":"Pending","summary":None,"ticks":0,"resource":"cpu",
          "resource_pretty":"CPU","ticket_id":None, "ticket_no":None,
          "ticket_href":None,"submitters":["userQ"], 'other': {'notes': 0}},
        {"account":"def-ccc-aa","claimant":None,"cluster":"testcluster2",
          "epoch":25,"id":11,"jobrange":[17,27],"pain":2.5,"state":"pending",
          "state_pretty":"Pending","summary":None,"ticks":0,"resource":"cpu",
          "resource_pretty":"CPU","ticket_id":None, "ticket_no":None,
          "ticket_href":None,"submitters":["userQ"], 'other': {'notes': 0}}
      ],
      "epoch":25
    }
  }

def test_get_events(client):
  """
  Get events related to a burst.
  """
  # log in
  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'user1'})
  assert response.status_code == 200

  # get events
  response = client.get('/xhr/bursts/13/events/')
  assert response.status_code == 200
  x = json.loads(response.data)

  # we don't really need to delete IDs but we do need to delete timestamps
  # because SQLite and Postgres report them differently
  del x[0]['id']
  del x[0]['timestamp']
  del x[1]['id']
  del x[1]['timestamp']
  del x[2]['id']
  del x[2]['timestamp']
  del x[3]['id']
  del x[3]['timestamp']
  print(x)
  assert x == [
    {
      'burstID': 13,
      'type': 'StateUpdate',
      'analyst': 'tst-003',
      'analyst_pretty': 'User 1',
      'old_state': 'pending',
      'new_state': 'rejected',
      'text': 'Hey how are ya',
    },
    {
      'burstID': 13,
      'type': 'Note',
      'analyst': 'tst-003',
      'analyst_pretty': 'User 1',
      'text': 'I just dinnae aboot this guy',
    },
    {
      'burstID': 13,
      'type': 'ClaimantUpdate',
      'analyst': 'tst-003',
      'analyst_pretty': 'User 1',
      'text': 'This is not the way',
      'claimant_was': None,
      'claimant_now': 'tst-003',
      'claimant_now_pretty': 'User 1',
    },
    {
      'burstID':13,
      'type': 'StateUpdate',
      'analyst': 'tst-003',
      'analyst_pretty': 'User 1',
      'text': 'Reverting to &lt;b&gt;pending&lt;/b&gt;',
      'old_state': 'rejected',
      'new_state': 'pending',
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
  response = client.get('/xhr/bursts/1/events/')
  assert response.status_code == 200
  x = json.loads(response.data)

  # we don't really need to delete IDs but we do need to delete timestamps
  # because SQLite and Postgres report them differently
  print(x)
  assert x == []

def test_update_bursts_xhr_no_timestamps(client):
  data = [
    {
      'id':13,
      'note': 'Stupid note',
      'state': 'rejected',
    },
    {
      'id':13,
      'note': 'Reverting to pending again',
      'state': 'pending',
    },
    {
      'id': 13,
      'note': 'This is not the way of the leaf',
      'claimant': 'tst-003',
    },
    {
      'id': 13,
      'note': 'I just do not ascertain this chap',
    },
  ]
  response = client.patch('/xhr/bursts/', json=data, environ_base={'HTTP_X_AUTHENTICATED_USER': 'user1'})
  print(response.data)
  assert response.status_code == 200
