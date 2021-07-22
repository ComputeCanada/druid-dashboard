# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=line-too-long
#
import time
import json
import pytest
from tests.tests_20_api import api_get, api_post

# ---------------------------------------------------------------------------
#                                                                API TESTS
# ---------------------------------------------------------------------------

def test_get_oldjobs_but_there_are_none(client):

  response = api_get(client, '/api/cases/?report=oldjobs')
  assert response.status_code == 200
  x = json.loads(response.data)
  assert x is None

def test_post_incomplete_oldjob_no_account(client):

  response = api_post(client, '/api/cases/', {
    'version': 2,
    'oldjobs': [
      {
        'resource': 'cpu',
        'age': 102,
        'summary': None,
        'submitter': 'userQ'
      }
    ]})
  assert response.status_code == 400
  print(response.data)
  assert json.loads(response.data) == {
    "detail": "Does not conform to API for report type oldjobs: Missing required field: \'account\'",
    "status": 400
  }

def test_post_incomplete_oldjob_no_age(client):

  response = api_post(client, '/api/cases/', {
    'version': 2,
    'oldjobs': [
      {
        'account': 'def-dleske',
        'resource': 'cpu',
        'summary': None,
        'submitter': 'userQ'
      }
    ]})
  assert response.status_code == 400
  assert json.loads(response.data) == {
    "detail": "Does not conform to API for report type oldjobs: Missing required field: \'age\'",
    "status": 400
  }

def test_post_incomplete_oldjob_no_resource(client):

  response = api_post(client, '/api/cases/', {
    'version': 2,
    'oldjobs': [
      {
        'account': 'def-dleske',
        'age': 120,
        'summary': None,
        'submitter': 'userQ'
      }
    ]})
  assert response.status_code == 400
  assert json.loads(response.data) == {
    "detail": "Does not conform to API for report type oldjobs: Missing required field: \'resource\'",
    "status": 400
  }

def test_post_incomplete_oldjob_no_summary(client):

  response = api_post(client, '/api/cases/', {
    'version': 2,
    'oldjobs': [
      {
        'account': 'def-dleske',
        'age': 120,
        'resource': 'cpu',
        'submitter': 'userQ'
      }
    ]})
  assert response.status_code == 400
  assert json.loads(response.data) == {
    "detail": "Does not conform to API for report type oldjobs: Missing required field: \'summary\'",
    "status": 400
  }

def test_post_incomplete_oldjob_no_submitter(client):

  response = api_post(client, '/api/cases/', {
    'version': 2,
    'oldjobs': [
      {
        'account': 'def-dleske',
        'age': 120,
        'resource': 'cpu',
        'summary': None,
      }
    ]})
  assert response.status_code == 400
  assert json.loads(response.data) == {
    "detail": "Does not conform to API for report type oldjobs: Missing required field: \'submitter\'",
    "status": 400
  }

def test_post_bad_oldjob_bad_resource(client):

  response = api_post(client, '/api/cases/', {
    'version': 2,
    'oldjobs': [
      {
        'account': 'def-dleske',
        'resource': 'ppu',
        'age': 120,
        'summary': None,
        'submitter': 'userQ'
      }
    ]})
  assert response.status_code == 400
  assert json.loads(response.data) == {
    "detail": "Does not conform to API for report type oldjobs: Invalid resource type: 'ppu'",
    "status": 400
  }

def test_post_empty_oldjob_report(client):
  """
  Tests that a report with no oldjobs is accepted as valid.
  """

  response = api_post(client, '/api/cases/', {
    'version': 2,
    'oldjobs': []
  })
  assert response.status_code == 201

def test_get_oldjobs_but_there_are_none_after_incomplete_posts(client):

  response = api_get(client, '/api/cases/?report=oldjobs')
  assert response.status_code == 200
  x = json.loads(response.data)
  assert x is None

def test_post_oldjob(client):

  response = api_post(client, '/api/cases/', {
    'version': 2,
    'oldjobs': [
      {
        'account': 'def-dleske',
        'resource': 'cpu',
        'age': 120,
        'summary': None,
        'submitter': 'userQ'
      }
    ]})
  assert response.status_code == 201

  response = api_get(client, '/api/cases/?report=oldjobs')
  assert response.status_code == 200
  parsed = json.loads(response.data)

  # remove mutable stuff (epoch)
  print(parsed)
  del parsed['epoch']
  del parsed['results'][0]['epoch']
  assert parsed == {
    'actions': None,
    'results': [
      {
        'id': 4,
        'cluster': 'testcluster',
        'account': 'def-dleske',
        'resource': 'cpu',
        'resource_pretty': 'CPU',
        'age': 120,
        'summary': None,
        'summary_pretty': '',
        'submitter': 'userQ',
        'ticks': 1,
        'ticket': None,
        'ticket_id': None,
        'ticket_no': None,
        'claimant': None,
        'other': {
          'notes': 0
        },
      }
    ]
  }

  # login as regular client
  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'user1'})
  assert response.status_code == 200

  # retrieve cases via AJAX
  response = client.get('/xhr/cases/?cluster=testcluster')
  assert response.status_code == 200
  parsed = json.loads(response.data)

  # remove mutable stuff (epoch)
  del parsed['oldjobs']['epoch']
  del parsed['oldjobs']['results'][0]['epoch']

  # test just oldjobs results
  assert parsed['oldjobs'] == {
    'actions': None,
    'results': [
      {
        'account': 'def-dleske',
        'claimant': None,
        'cluster': 'testcluster',
        'id': 4,
        'other': {'notes': 0},
        'age': 120,
        'resource': 'cpu',
        'resource_pretty': 'CPU',
        'submitter': 'userQ',
        'summary': None,
        'summary_pretty': '',
        'ticket': None,
        'ticket_id': None,
        'ticket_no': None,
        'ticks': 1
      }
    ]
  }

@pytest.mark.dependency(name='oldjobs_posted')
def test_post_oldjobs(client, notifier):

  response = api_post(client, '/api/cases/', {
    'version': 2,
    'oldjobs': [
      {
        'account': 'def-dleske',
        'resource': 'cpu',
        'age': 121,
        'summary': None,
        'submitter': 'userX'
      },
      {
        'account': 'def-bobaloo-aa',
        'resource': 'cpu',
        'age': 612,
        'summary': None,
        'submitter': 'userX'
      }
    ]})
  assert response.status_code == 201

  response = api_get(client, '/api/cases/?report=oldjobs')
  assert response.status_code == 200
  parsed = json.loads(response.data)

  # remove mutable stuff (epoch)
  print(parsed)
  del parsed['epoch']
  del parsed['results'][0]['epoch']
  del parsed['results'][1]['epoch']
  assert parsed == {
    'actions': None,
    'results': [
      {
        'id': 4,
        'cluster': 'testcluster',
        'account': 'def-dleske',
        'resource': 'cpu',
        'resource_pretty': 'CPU',
        'age': 121,
        'summary': None,
        'summary_pretty': '',
        'submitter': 'userX',
        'ticks': 2,
        'ticket': None,
        'ticket_id': None,
        'ticket_no': None,
        'claimant': None,
        'other': {
          'notes': 0
        },
      },
      {
        'id': 5,
        'cluster': 'testcluster',
        'account': 'def-bobaloo-aa',
        'resource': 'cpu',
        'resource_pretty': 'CPU',
        'age': 612,
        'summary': None,
        'summary_pretty': '',
        'submitter': 'userX',
        'ticks': 1,
        'ticket': None,
        'ticket_id': None,
        'ticket_no': None,
        'claimant': None,
        'other': {
          'notes': 0
        },
      }
    ]
  }

  print(notifier.notifications[-2:])
  assert notifier.notifications[-2:] == [
    'beam-dev: ReportReceived: oldjobs on testcluster: There are 1 cases (1 new and 0 existing).  0 are claimed.',
    'beam-dev: ReportReceived: oldjobs on testcluster: There are 2 cases (1 new and 1 existing).  0 are claimed.'
  ]

@pytest.mark.dependency(depends=['oldjobs_posted'])
def test_get_oldjobs(client):

  response = api_get(client, '/api/cases/?report=oldjobs')
  assert response.status_code == 200
  x = json.loads(response.data)
  assert x is not None

def test_get_non_existent_oldjob(client):

  response = api_get(client, '/api/cases/11')
  assert response.status_code == 404

@pytest.mark.dependency(depends=['oldjobs_posted'])
def test_get_oldjob(client):

  id = 4
  response = api_get(client, f'/api/cases/{id}')
  assert response.status_code == 200
  x = json.loads(response.data)
  del x['epoch']
  print(x)
  assert x == {
    'account': 'def-dleske',
    'resource': 'cpu',
    'claimant': None,
    'cluster': 'testcluster',
    'id': id,
    'age': 121,
    'summary': None,
    'ticket_id': None,
    'ticket_no': None,
    'ticks': 2,
    'submitter': 'userX',
    'other': {'notes': 0}
  }

@pytest.mark.dependency(depends=['oldjobs_posted'])
def test_post_oldjobs_updated(client, notifier):

  # SQLite uses second-accuracy time so for consistency we do the same with
  # Postgres.  In testing we need to introduce a 1s delay to force the
  # following update to be of a different epoch than what we did above.
  time.sleep(1)

  response = api_post(client, '/api/cases/', {
    'version': 2,
    'oldjobs': [
      {
        'account': 'def-dleske',
        'resource': 'cpu',
        'age': 122,
        'summary': None,
        'submitter': 'userQ'
      }
    ]})
  assert response.status_code == 201

  print(notifier.notifications[-3:])
  assert notifier.notifications[-3:] == [
    'beam-dev: ReportReceived: oldjobs on testcluster: There are 1 cases (1 new and 0 existing).  0 are claimed.',
    'beam-dev: ReportReceived: oldjobs on testcluster: There are 2 cases (1 new and 1 existing).  0 are claimed.',
    'beam-dev: ReportReceived: oldjobs on testcluster: There are 1 cases (0 new and 1 existing).  0 are claimed.'
  ]

  # now login and retrieve oldjob candidates as manager would
  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'admin1'})
  assert response.status_code == 302
  response = client.get('/xhr/cases/?cluster=testcluster')
  assert response.status_code == 200
  parsed = json.loads(response.data)
  print(parsed)

  # test we see what we should and not what we shouldn't
  assert parsed['cluster'] == 'testcluster'
  for oldjob in parsed['oldjobs']['results']:
    if oldjob['account'] == 'def-dleske':
      # assert age was updated
      assert oldjob['age'] == 122
    else:
      # we should _not_ see the "bobaloo" account because it was in the
      # previous epoch and so no longer current
      assert oldjob['account'] != 'def-bobaloo-aa'

def test_post_oldjobs_with_other_updates(client, notifier):
  """
  Tests that state and claimant information in notification is correct.
  """

  id = 4
  data = [
    {
      'note': 'This is not the way',
      'datum': 'claimant',
      'value': 'tst-003',
      'timestamp':'2019-03-31 10:35 AM'
    }
  ]

  response = client.patch('/xhr/cases/{}'.format(id), json=data, environ_base={'HTTP_X_AUTHENTICATED_USER': 'user1'})
  print(json.loads(response.data))
  assert response.status_code == 200

  response = api_post(client, '/api/cases/', {
    'version': 2,
    'oldjobs': [
      {
        'account': 'def-dleske',
        'resource': 'cpu',
        'age': 122,
        'summary': None,
        'submitter': 'userQ'
      },
      {
        'account': 'def-bobaloo-aa',
        'resource': 'cpu',
        'age': 612,
        'summary': None,
        'submitter': 'userQ'
      }
    ]})
  assert response.status_code == 201

  response = api_get(client, '/api/cases/{}'.format(id))
  print(json.loads(response.data))

  print(notifier.notifications[-4:])
  assert notifier.notifications[-4:] == [
    'beam-dev: ReportReceived: oldjobs on testcluster: There are 1 cases (1 new and 0 existing).  0 are claimed.',
    'beam-dev: ReportReceived: oldjobs on testcluster: There are 2 cases (1 new and 1 existing).  0 are claimed.',
    'beam-dev: ReportReceived: oldjobs on testcluster: There are 1 cases (0 new and 1 existing).  0 are claimed.',
    'beam-dev: ReportReceived: oldjobs on testcluster: There are 2 cases (0 new and 2 existing).  1 are claimed.'
  ]
