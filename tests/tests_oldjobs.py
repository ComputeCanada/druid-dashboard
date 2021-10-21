# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=line-too-long,no-self-use
#
import time
import json
from tests.tests_api import api_get, api_post

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
        'account': 'def-pi1',
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
        'account': 'def-pi1',
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
        'account': 'def-pi1',
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
        'account': 'def-pi1',
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
        'account': 'def-pi1',
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

class TestPostingOldJobs:

  def test_post_oldjob(self, client):

    response = api_post(client, '/api/cases/', {
      'version': 2,
      'oldjobs': [
        {
          'account': 'def-pi1',
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
      'results': [
        {
          'id': 2,
          'cluster': 'testcluster',
          'account': 'def-pi1',
          'resource': 'cpu',
          'age': 120,
          'summary': None,
          'submitter': 'userQ',
          'ticks': 1,
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
      'results': [
        {
          'account': 'def-pi1',
          'claimant': None,
          'cluster': 'testcluster',
          'id': 2,
          'other': {'notes': 0},
          'age': 120,
          'resource': 'cpu',
          'resource_pretty': 'CPU',
          'submitter': 'userQ',
          'summary': None,
          'ticket': None,
          'ticket_id': None,
          'ticket_no': None,
          'ticks': 1
        }
      ]
    }

  def test_post_oldjobs(self, client, notifier):

    response = api_post(client, '/api/cases/', {
      'version': 2,
      'oldjobs': [
        {
          'account': 'def-pi1',
          'resource': 'cpu',
          'age': 121,
          'summary': None,
          'submitter': 'userX'
        },
        {
          'account': 'def-pi2-ab',
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
      'results': [
        {
          'id': 2,
          'cluster': 'testcluster',
          'account': 'def-pi1',
          'resource': 'cpu',
          'age': 121,
          'summary': None,
          'submitter': 'userX',
          'ticks': 2,
          'ticket_id': None,
          'ticket_no': None,
          'claimant': None,
          'other': {
            'notes': 0
          },
        },
        {
          'id': 3,
          'cluster': 'testcluster',
          'account': 'def-pi2-ab',
          'resource': 'cpu',
          'age': 612,
          'summary': None,
          'submitter': 'userX',
          'ticks': 1,
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

  def test_get_oldjobs(self, client):

    response = api_get(client, '/api/cases/?report=oldjobs')
    assert response.status_code == 200
    x = json.loads(response.data)
    assert x is not None

  def test_get_oldjob(self, client):

    id = 2
    response = api_get(client, f'/api/cases/{id}')
    assert response.status_code == 200
    x = json.loads(response.data)
    del x['epoch']
    print(x)
    assert x == {
      'account': 'def-pi1',
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

  def test_post_oldjobs_updated(self, client, notifier):

    # SQLite uses second-accuracy time so for consistency we do the same with
    # Postgres.  In testing we need to introduce a 1s delay to force the
    # following update to be of a different epoch than what we did above.
    time.sleep(1)

    response = api_post(client, '/api/cases/', {
      'version': 2,
      'oldjobs': [
        {
          'account': 'def-pi1',
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
    response = client.get('/xhr/cases/?cluster=testcluster')
    assert response.status_code == 200
    parsed = json.loads(response.data)
    print(parsed)

    # test we see what we should and not what we shouldn't
    assert parsed['cluster'] == 'testcluster'
    for oldjob in parsed['oldjobs']['results']:
      if oldjob['account'] == 'def-pi1':
        # assert age was updated
        assert oldjob['age'] == 122
      else:
        # we should _not_ see the "bobaloo" account because it was in the
        # previous epoch and so no longer current
        assert oldjob['account'] != 'def-pi2-ab'

  def test_post_oldjobs_with_other_updates(self, client, notifier):
    """
    Tests that state and claimant information in notification is correct.
    """

    id = 2
    data = [
      {
        'note': 'This is not the way',
        'claimant': 'tst-003',
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
          'account': 'def-pi1',
          'resource': 'cpu',
          'age': 122,
          'summary': None,
          'submitter': 'userQ'
        },
        {
          'account': 'def-pi2-ab',
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

  def test_post_oldjobs_updated_with_summary(self, client):

    response = api_post(client, '/api/cases/', {
      'version': 2,
      'oldjobs': [
        {
          'account': 'def-pi1',
          'resource': 'cpu',
          'age': 123,
          'summary': {
            'thing': 'thong'
          },
          'submitter': 'userQ'
        }
      ]})
    assert response.status_code == 201

    # now login and retrieve oldjob candidates as manager would
    response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'admin1'})
    response = client.get('/xhr/cases/?cluster=testcluster')
    assert response.status_code == 200
    parsed = json.loads(response.data)
    print(parsed)

    # test we see what we should and not what we shouldn't
    assert parsed['cluster'] == 'testcluster'
    for oldjob in parsed['oldjobs']['results']:
      if oldjob['account'] == 'def-pi1':
        # assert summary is valid
        assert oldjob['summary'] == { 'thing': 'thong' }

def test_get_non_existent_oldjob(client):

  response = api_get(client, '/api/cases/11')
  assert response.status_code == 404

def test_post_oldjobs_and_bursts_at_once(client, notifier):

  response = api_post(client, '/api/cases/', {
    'version': 2,
    'oldjobs': [
      {
        'account': 'def-pi1',
        'resource': 'cpu',
        'age': 121,
        'summary': None,
        'submitter': 'userX'
      },
      {
        'account': 'def-pi2-ab',
        'resource': 'cpu',
        'age': 612,
        'summary': None,
        'submitter': 'userX'
      }
    ],
    'bursts': [
      {
        'account': 'def-pi1',
        'resource': 'cpu',
        'pain': 70.4,
        'summary': {
          'cpus_total': 100,
          'jobs_total': 50,
          'mem_total': 200,
        },
        'firstjob': 20000,
        'lastjob': 20500,
        'submitters': [
          'userX'
        ]
      },
      {
        'account': 'def-pi2-ab',
        'resource': 'cpu',
        'pain': 90.412,
        'summary': {
          'cpus_total': 200,
          'jobs_total': 50,
          'mem_total': 100,
        },
        'firstjob': 20001,
        'lastjob': 20541,
        'submitters': [
          'userX',
          'userQ'
        ]
      }
    ]})
  assert response.status_code == 201

  # retrieve cases via AJAX
  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'user1'})
  assert response.status_code == 200
  response = client.get('/xhr/cases/?cluster=testcluster')
  assert response.status_code == 200
  parsed = json.loads(response.data)

  # remove mutable stuff (epoch)
  del parsed['oldjobs']['epoch']
  del parsed['oldjobs']['results'][0]['epoch']
  del parsed['oldjobs']['results'][0]['id']
  del parsed['oldjobs']['results'][1]['epoch']
  del parsed['oldjobs']['results'][1]['id']
  print(parsed['oldjobs'])

  # test just oldjobs results
  assert parsed['oldjobs'] == {
    'results': [
      {
        'account': 'def-pi1',
        'claimant': None,
        'cluster': 'testcluster',
        'other': {'notes': 0},
        'age': 121,
        'resource': 'cpu',
        'resource_pretty': 'CPU',
        'submitter': 'userX',
        'summary': None,
        'ticket': None,
        'ticket_id': None,
        'ticket_no': None,
        'ticks': 1
      },
      {
        'account': 'def-pi2-ab',
        'claimant': None,
        'cluster': 'testcluster',
        'other': { 'notes': 0 },
        'age': 612,
        'resource': 'cpu',
        'resource_pretty': 'CPU',
        'submitter': 'userX',
        'summary': None,
        'ticket': None,
        'ticket_id': None,
        'ticket_no': None,
        'ticks': 1,
      }
    ]
  }

  # remove mutable stuff (epoch)
  del parsed['bursts']['epoch']
  del parsed['bursts']['results'][0]['epoch']
  del parsed['bursts']['results'][0]['id']
  del parsed['bursts']['results'][1]['epoch']
  del parsed['bursts']['results'][1]['id']
  print(parsed['bursts'])

  # test just bursts results
  assert parsed['bursts'] == {
    'results': [
      {
        'account': 'def-pi1',
        'actions': [{'id': 'reject', 'label': 'Reject'}],
        'claimant': None,
        'cluster': 'testcluster',
        'jobrange': [20000, 20500],
        'other': {
          'notes': 0
        },
        'pain': 70.4,
        'pain_pretty': '70.40',
        'resource': 'cpu',
        'resource_pretty': 'CPU',
        'state': 'pending',
        'state_pretty': 'Pending',
        'submitters': ['userX'],
        'summary': {
          'cpus_total': 100,
          'jobs_total': 50,
          'mem_total': 200,
        },
        'summary_pretty': '<table><tr><th>cpus_total</th><td>100</td></tr><tr><th>jobs_total</th><td>50</td></tr><tr><th>mem_total</th><td>200</td></tr></table>',
        'ticket': None,
        'ticket_id': None,
        'ticket_no': None,
        'ticks': 1,
        'usage_pretty': '<a target="beamplot" href="https://localhost/plots/testcluster/def-pi1_cpu_cumulative.html">Cumulative</a>\n    <br/>\n    <a target="beamplot" href="https://localhost/plots/testcluster/def-pi1_cpu_instant.html">Instant</a>'
      },
      {
        'account': 'def-pi2-ab',
        'actions': [{'id': 'reject', 'label': 'Reject'}],
        'claimant': None,
        'cluster': 'testcluster',
        'jobrange': [20001, 20541],
        'other': {
          'notes': 0
        },
        'pain': 90.412,
        'pain_pretty': '90.41',
        'resource': 'cpu',
        'resource_pretty': 'CPU',
        'state': 'pending',
        'state_pretty': 'Pending',
        'submitters': ['userX', 'userQ'],
        'summary': {
          'cpus_total': 200,
          'jobs_total': 50,
          'mem_total': 100,
        },
        'summary_pretty': '<table><tr><th>cpus_total</th><td>200</td></tr><tr><th>jobs_total</th><td>50</td></tr><tr><th>mem_total</th><td>100</td></tr></table>',
        'ticket': None,
        'ticket_id': None,
        'ticket_no': None,
        'ticks': 1,
        'usage_pretty': '<a target="beamplot" href="https://localhost/plots/testcluster/def-pi2-ab_cpu_cumulative.html">Cumulative</a>\n    <br/>\n    <a target="beamplot" href="https://localhost/plots/testcluster/def-pi2-ab_cpu_instant.html">Instant</a>'
      }
    ]
  }

  response = api_get(client, '/api/cases/?report=bursts')
  assert response.status_code == 200
  parsed = json.loads(response.data)

  # remove mutable stuff (epoch)
  del parsed['epoch']
  del parsed['results'][0]['epoch']
  del parsed['results'][1]['epoch']
  del parsed['results'][0]['id']
  del parsed['results'][1]['id']
  print(parsed)
  assert parsed == {
    'results': [
      {
        'account': 'def-pi1',
        'claimant': None,
        'cluster': 'testcluster',
        'jobrange': [20000, 20500],
        'other': {
          'notes': 0
        },
        'pain': 70.4,
        'resource': 'cpu',
        'state': 'pending',
        'submitters': ['userX'],
        'summary': {
          'cpus_total': 100,
          'jobs_total': 50,
          'mem_total': 200,
        },
        'ticket_id': None,
        'ticket_no': None,
        'ticks': 1,
      },
      {
        'account': 'def-pi2-ab',
        'claimant': None,
        'cluster': 'testcluster',
        'jobrange': [20001, 20541],
        'other': {
          'notes': 0
        },
        'pain': 90.412,
        'resource': 'cpu',
        'state': 'pending',
        'submitters': ['userX', 'userQ'],
        'summary': {
          'cpus_total': 200,
          'jobs_total': 50,
          'mem_total': 100,
        },
        'ticket_id': None,
        'ticket_no': None,
        'ticks': 1,
      }
    ]
  }

  response = api_get(client, '/api/cases/?report=oldjobs')
  assert response.status_code == 200
  parsed = json.loads(response.data)

  # remove mutable stuff (epoch)
  del parsed['epoch']
  del parsed['results'][0]['epoch']
  del parsed['results'][1]['epoch']
  del parsed['results'][0]['id']
  del parsed['results'][1]['id']
  print(parsed)
  assert parsed == {
    'results': [
      {
        'cluster': 'testcluster',
        'account': 'def-pi1',
        'resource': 'cpu',
        'age': 121,
        'summary': None,
        'submitter': 'userX',
        'ticks': 1,
        'ticket_id': None,
        'ticket_no': None,
        'claimant': None,
        'other': {
          'notes': 0
        },
      },
      {
        'cluster': 'testcluster',
        'account': 'def-pi2-ab',
        'resource': 'cpu',
        'age': 612,
        'summary': None,
        'submitter': 'userX',
        'ticks': 1,
        'ticket_id': None,
        'ticket_no': None,
        'claimant': None,
        'other': {
          'notes': 0
        },
      }
    ]
  }

  print(notifier.notifications)
  assert notifier.notifications == [
    'beam-dev: ReportReceived: bursts on testcluster: 2 new record(s) and 0 existing.  In total there are 2 pending, 0 accepted, 0 rejected.  0 have been claimed.',
    'beam-dev: ReportReceived: oldjobs on testcluster: There are 2 cases (2 new and 0 existing).  0 are claimed.'
  ]

def test_post_oldjobs_and_bursts_first_one_then_the_other(client, notifier):

  response = api_post(client, '/api/cases/', {
    'version': 2,
    'bursts': [
      {
        'account': 'def-pi1',
        'resource': 'cpu',
        'pain': 70.4,
        'summary': {
          'cpus_total': 100,
          'jobs_total': 50,
          'mem_total': 200,
        },
        'firstjob': 20000,
        'lastjob': 20500,
        'submitters': [
          'userX'
        ]
      },
      {
        'account': 'def-pi2-ab',
        'resource': 'cpu',
        'pain': 90.412,
        'summary': {
          'cpus_total': 200,
          'jobs_total': 50,
          'mem_total': 100,
        },
        'firstjob': 20001,
        'lastjob': 20541,
        'submitters': [
          'userX',
          'userQ'
        ]
      }
    ]})
  assert response.status_code == 201

  time.sleep(1)
  response = api_post(client, '/api/cases/', {
    'version': 2,
    'oldjobs': [
      {
        'account': 'def-pi1',
        'resource': 'cpu',
        'age': 121,
        'summary': None,
        'submitter': 'userX'
      },
      {
        'account': 'def-pi2-ab',
        'resource': 'cpu',
        'age': 612,
        'summary': None,
        'submitter': 'userX'
      }
    ]})
  assert response.status_code == 201

  # retrieve cases via AJAX
  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'user1'})
  assert response.status_code == 200
  response = client.get('/xhr/cases/?cluster=testcluster')
  assert response.status_code == 200
  parsed = json.loads(response.data)

  # remove mutable stuff (epoch)
  del parsed['oldjobs']['epoch']
  del parsed['oldjobs']['results'][0]['epoch']
  del parsed['oldjobs']['results'][0]['id']
  del parsed['oldjobs']['results'][1]['epoch']
  del parsed['oldjobs']['results'][1]['id']
  print(parsed['oldjobs'])

  # test just oldjobs results
  assert parsed['oldjobs'] == {
    'results': [
      {
        'account': 'def-pi1',
        'claimant': None,
        'cluster': 'testcluster',
        'other': {'notes': 0},
        'age': 121,
        'resource': 'cpu',
        'resource_pretty': 'CPU',
        'submitter': 'userX',
        'summary': None,
        'ticket': None,
        'ticket_id': None,
        'ticket_no': None,
        'ticks': 1
      },
      {
        'account': 'def-pi2-ab',
        'claimant': None,
        'cluster': 'testcluster',
        'other': { 'notes': 0 },
        'age': 612,
        'resource': 'cpu',
        'resource_pretty': 'CPU',
        'submitter': 'userX',
        'summary': None,
        'ticket': None,
        'ticket_id': None,
        'ticket_no': None,
        'ticks': 1,
      }
    ]
  }

  # remove mutable stuff (epoch)
  del parsed['bursts']['epoch']
  del parsed['bursts']['results'][0]['epoch']
  del parsed['bursts']['results'][0]['id']
  del parsed['bursts']['results'][1]['epoch']
  del parsed['bursts']['results'][1]['id']
  print(parsed['bursts'])

  # test just bursts results
  assert parsed['bursts'] == {
    'results': [
      {
        'account': 'def-pi1',
        'actions': [{'id': 'reject', 'label': 'Reject'}],
        'claimant': None,
        'cluster': 'testcluster',
        'jobrange': [20000, 20500],
        'other': {
          'notes': 0
        },
        'pain': 70.4,
        'pain_pretty': '70.40',
        'resource': 'cpu',
        'resource_pretty': 'CPU',
        'state': 'pending',
        'state_pretty': 'Pending',
        'submitters': ['userX'],
        'summary': {
          'cpus_total': 100,
          'jobs_total': 50,
          'mem_total': 200,
        },
        'summary_pretty': '<table><tr><th>cpus_total</th><td>100</td></tr><tr><th>jobs_total</th><td>50</td></tr><tr><th>mem_total</th><td>200</td></tr></table>',
        'ticket': None,
        'ticket_id': None,
        'ticket_no': None,
        'ticks': 1,
        'usage_pretty': '<a target="beamplot" href="https://localhost/plots/testcluster/def-pi1_cpu_cumulative.html">Cumulative</a>\n    <br/>\n    <a target="beamplot" href="https://localhost/plots/testcluster/def-pi1_cpu_instant.html">Instant</a>'
      },
      {
        'account': 'def-pi2-ab',
        'actions': [{'id': 'reject', 'label': 'Reject'}],
        'claimant': None,
        'cluster': 'testcluster',
        'jobrange': [20001, 20541],
        'other': {
          'notes': 0
        },
        'pain': 90.412,
        'pain_pretty': '90.41',
        'resource': 'cpu',
        'resource_pretty': 'CPU',
        'state': 'pending',
        'state_pretty': 'Pending',
        'submitters': ['userX', 'userQ'],
        'summary': {
          'cpus_total': 200,
          'jobs_total': 50,
          'mem_total': 100,
        },
        'summary_pretty': '<table><tr><th>cpus_total</th><td>200</td></tr><tr><th>jobs_total</th><td>50</td></tr><tr><th>mem_total</th><td>100</td></tr></table>',
        'ticket': None,
        'ticket_id': None,
        'ticket_no': None,
        'ticks': 1,
        'usage_pretty': '<a target="beamplot" href="https://localhost/plots/testcluster/def-pi2-ab_cpu_cumulative.html">Cumulative</a>\n    <br/>\n    <a target="beamplot" href="https://localhost/plots/testcluster/def-pi2-ab_cpu_instant.html">Instant</a>'
      }
    ]
  }

  response = api_get(client, '/api/cases/?report=bursts')
  assert response.status_code == 200
  parsed = json.loads(response.data)

  # remove mutable stuff (epoch)
  del parsed['epoch']
  del parsed['results'][0]['epoch']
  del parsed['results'][1]['epoch']
  del parsed['results'][0]['id']
  del parsed['results'][1]['id']
  print(parsed)
  assert parsed == {
    'results': [
      {
        'account': 'def-pi1',
        'claimant': None,
        'cluster': 'testcluster',
        'jobrange': [20000, 20500],
        'other': {
          'notes': 0
        },
        'pain': 70.4,
        'resource': 'cpu',
        'state': 'pending',
        'submitters': ['userX'],
        'summary': {
          'cpus_total': 100,
          'jobs_total': 50,
          'mem_total': 200,
        },
        'ticket_id': None,
        'ticket_no': None,
        'ticks': 1,
      },
      {
        'account': 'def-pi2-ab',
        'claimant': None,
        'cluster': 'testcluster',
        'jobrange': [20001, 20541],
        'other': {
          'notes': 0
        },
        'pain': 90.412,
        'resource': 'cpu',
        'state': 'pending',
        'submitters': ['userX', 'userQ'],
        'summary': {
          'cpus_total': 200,
          'jobs_total': 50,
          'mem_total': 100,
        },
        'ticket_id': None,
        'ticket_no': None,
        'ticks': 1,
      }
    ]
  }

  response = api_get(client, '/api/cases/?report=oldjobs')
  assert response.status_code == 200
  parsed = json.loads(response.data)

  # remove mutable stuff (epoch)
  del parsed['epoch']
  del parsed['results'][0]['epoch']
  del parsed['results'][1]['epoch']
  del parsed['results'][0]['id']
  del parsed['results'][1]['id']
  print(parsed)
  assert parsed == {
    'results': [
      {
        'cluster': 'testcluster',
        'account': 'def-pi1',
        'resource': 'cpu',
        'age': 121,
        'summary': None,
        'submitter': 'userX',
        'ticks': 1,
        'ticket_id': None,
        'ticket_no': None,
        'claimant': None,
        'other': {
          'notes': 0
        },
      },
      {
        'cluster': 'testcluster',
        'account': 'def-pi2-ab',
        'resource': 'cpu',
        'age': 612,
        'summary': None,
        'submitter': 'userX',
        'ticks': 1,
        'ticket_id': None,
        'ticket_no': None,
        'claimant': None,
        'other': {
          'notes': 0
        },
      }
    ]
  }

  print(notifier.notifications)
  assert notifier.notifications == [
    'beam-dev: ReportReceived: bursts on testcluster: 2 new record(s) and 0 existing.  In total there are 2 pending, 0 accepted, 0 rejected.  0 have been claimed.',
    'beam-dev: ReportReceived: oldjobs on testcluster: There are 2 cases (2 new and 0 existing).  0 are claimed.'
  ]
