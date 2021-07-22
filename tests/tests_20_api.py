# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=line-too-long
#
import time
from email.utils import formatdate
import hmac
import base64
import json
import pytest

from manager.api import API_VERSION

def api_get(client, resource, access=None, secret=None):

  # get current datestamp in RFC2822 format.  Without "localtime", will be
  # given a timezone of "-0000" which indicates, according to the RFC, that
  # nothing is known about the local time zone, offending the RFC (which
  # states that local time should be used) and resulting in a timezone-naive
  # RFC.  Yes, I'm annoyed how much time I spent figuring this out.
  timestamp = formatdate(localtime=True)

  # build request string to digest
  digestible = "GET {}\n{}".format(resource, timestamp)

  # test api key (since retrieving, use scheduler's key)
  if access is None:
    access = 'testapikey_s'
    secret = 'T3h5mwEk7mrVwxdon+s9blWhVh8zHDd7PVoUoWJsTf5Qd2EUie6I4pdBuyRykw=='

  # create digest
  h = hmac.new(secret.encode(), digestmod='sha256')
  h.update(digestible.encode())
  digest = base64.b64encode(h.digest()).decode('utf-8')

  # headers to add to request
  headers = {
    'Date': timestamp,
    'Authorization': "BEAM {} {}".format(access, digest)
  }

  return client.get(resource, headers=headers)

def api_post(client, resource, data):

  # need current timestamp in RFC2822 format.
  timestamp = formatdate(localtime=True)

  # build request string to digest
  digestible = "POST {}\n{}".format(resource, timestamp)

  # test api key (since posting, use detector's key)
  access = 'testapikey_d'
  secret = b'WuHheVDysQQwdb+NK98w8EOHdiNUjLlz2Uxg/kIHqIGOek4DAmC5NCd2gZv7RQ=='

  # create digest
  h = hmac.new(secret, digestmod='sha256')
  h.update(digestible.encode())
  digest = base64.b64encode(h.digest()).decode('utf-8')

  # headers to add to request
  headers = {
    'Date': timestamp,
    'Authorization': "BEAM {} {}".format(access, digest)
  }

  return client.post(resource, headers=headers, json=data)


# ---------------------------------------------------------------------------
#                                                                API TESTS
# ---------------------------------------------------------------------------

def test_api_unsigned(client):

  response = client.get('/api/cases/')
  assert response.status_code == 401

def test_get_bursts_but_there_are_none(client):

  response = api_get(client, '/api/cases/?report=bursts')
  assert response.status_code == 200
  x = json.loads(response.data)
  assert x is None

def test_post_nothing(client):

  response = api_post(client, '/api/cases/', {})
  assert response.status_code == 400
  assert response.data == b'{"error":"400 Bad Request: API violation: must define \'version\'"}\n'

def test_post_report_without_report(client):
  # In v2 of the API, this is valid

  response = api_post(client, '/api/cases/', {
    'version': 2
    })
  assert response.status_code == 200

def test_post_report_no_version(client):

  response = api_post(client, '/api/cases/', {
    'bursts': [
      {
        'account': 'def-dleske',
        'pain': 0.0,
        'firstjob': 1000,
        'lastjob': 2000,
        'summary': None,
      }
    ]})
  assert response.status_code == 400
  assert response.data == b'{"error":"400 Bad Request: API violation: must define \'version\'"}\n'

def test_post_report_old_version(client):
  # Note: version 0 of the API used "report" instead of "bursts", so using a
  # correct version 0 API call will trigger the wrong error response (in that
  # it's not the test response we want to test).
  response = api_post(client, '/api/cases/', {
    'version': 1,
    'bursts': [
      {
        'rapi': 'def-dleske',
        'pain': 0.0,
        'firstjob': 1000,
        'lastjob': 2000,
        'summary': None,
      }
    ]})

  expected = '{{"error":"400 Bad Request: Client API version (1) does not match server ({})"}}\n'.format(API_VERSION)

  assert response.status_code == 400
  assert response.data == expected.encode('utf-8')

def test_post_incomplete_burst_no_account(client):

  response = api_post(client, '/api/cases/', {
    'version': 2,
    'bursts': [
      {
        'resource': 'cpu',
        'pain': 0.0,
        'firstjob': 1000,
        'lastjob': 2000,
        'summary': None,
        'submitters': ['userQ']
      }
    ]})
  assert response.status_code == 400
  print(response.data)
  assert response.data == b'{"error":"400 Bad Request: Does not conform to API for report type bursts: Missing required field: \'account\'"}\n'

def test_post_incomplete_burst_no_firstjob(client):

  response = api_post(client, '/api/cases/', {
    'version': 2,
    'bursts': [
      {
        'account': 'def-dleske',
        'resource': 'cpu',
        'pain': 0.0,
        'lastjob': 2000,
        'summary': None,
        'submitters': ['userQ']
      }
    ]})
  assert response.status_code == 400
  assert response.data == b'{"error":"400 Bad Request: Does not conform to API for report type bursts: Missing required field: \'firstjob\'"}\n'

def test_post_incomplete_burst_no_lastjob(client):

  response = api_post(client, '/api/cases/', {
    'version': 2,
    'bursts': [
      {
        'account': 'def-dleske',
        'resource': 'cpu',
        'pain': 0.0,
        'firstjob': 1000,
        'summary': None,
        'submitters': ['userQ']
      }
    ]})
  assert response.status_code == 400
  assert response.data == b'{"error":"400 Bad Request: Does not conform to API for report type bursts: Missing required field: \'lastjob\'"}\n'

def test_post_incomplete_burst_no_pain(client):

  response = api_post(client, '/api/cases/', {
    'version': 2,
    'bursts': [
      {
        'account': 'def-dleske',
        'resource': 'cpu',
        'firstjob': 1000,
        'lastjob': 2000,
        'summary': None,
        'submitters': ['userQ']
      }
    ]})
  assert response.status_code == 400
  assert response.data == b'{"error":"400 Bad Request: Does not conform to API for report type bursts: Missing required field: \'pain\'"}\n'

def test_post_incomplete_burst_no_resource(client):

  response = api_post(client, '/api/cases/', {
    'version': 2,
    'bursts': [
      {
        'account': 'def-dleske',
        'pain': 0.0,
        'firstjob': 1000,
        'lastjob': 2000,
        'summary': None,
        'submitters': ['userQ']
      }
    ]})
  assert response.status_code == 400
  assert response.data == b'{"error":"400 Bad Request: Does not conform to API for report type bursts: Missing required field: \'resource\'"}\n'

def test_post_incomplete_burst_no_summary(client):

  response = api_post(client, '/api/cases/', {
    'version': 2,
    'bursts': [
      {
        'account': 'def-dleske',
        'resource': 'cpu',
        'pain': 0.0,
        'firstjob': 1000,
        'lastjob': 2000,
        'submitters': ['userQ']
      }
    ]})
  assert response.status_code == 400
  assert response.data == b'{"error":"400 Bad Request: Does not conform to API for report type bursts: Missing required field: \'summary\'"}\n'

def test_post_incomplete_burst_no_submitters(client):

  response = api_post(client, '/api/cases/', {
    'version': 2,
    'bursts': [
      {
        'account': 'def-dleske',
        'resource': 'cpu',
        'pain': 0.0,
        'firstjob': 1000,
        'lastjob': 2000,
        'summary': None,
      }
    ]})
  assert response.status_code == 400
  assert response.data == b'{"error":"400 Bad Request: Does not conform to API for report type bursts: Missing required field: \'submitters\'"}\n'

def test_post_bad_burst_bad_resource(client):

  response = api_post(client, '/api/cases/', {
    'version': 2,
    'bursts': [
      {
        'account': 'def-dleske',
        'resource': 'ppu',
        'pain': 0.0,
        'firstjob': 1000,
        'lastjob': 2000,
        'summary': None,
        'submitters': ['userQ']
      }
    ]})
  assert response.status_code == 400
  assert response.data == b'{"error":"400 Bad Request: Does not conform to API for report type bursts: Invalid resource type: \'ppu\'"}\n'

def test_post_empty_burst_report(client):
  """
  Tests that a report with no bursts is accepted as valid.
  """

  response = api_post(client, '/api/cases/', {
    'version': 2,
    'bursts': []
  })
  assert response.status_code == 201

def test_post_burst(client):

  response = api_post(client, '/api/cases/', {
    'version': 2,
    'bursts': [
      {
        'account': 'def-dleske',
        'resource': 'cpu',
        'pain': 0.0,
        'firstjob': 1000,
        'lastjob': 2000,
        'summary': None,
        'submitters': ['userQ']
      }
    ]})
  assert response.status_code == 201

  # this will actually be blank because this view only returns "ACCEPTED"
  # bursts
  response = api_get(client, '/api/cases/?report=bursts&view=adjustor')
  assert response.status_code == 200
  parsed = json.loads(response.data)
  assert parsed is None

  # login as regular client
  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'user1'})
  assert response.status_code == 200

  # retrieve cases via AJAX
  response = client.get('/xhr/cases/?cluster=testcluster')
  assert response.status_code == 200
  parsed = json.loads(response.data)

  # remove mutable stuff (epoch)
  del parsed['bursts']['epoch']
  del parsed['bursts']['results'][0]['epoch']
  print(parsed)

  assert parsed == {
    'cluster': 'testcluster',
    'bursts': {
      'actions': None,
      'results': [
        {
          'account': 'def-dleske',
          'claimant': None,
          'cluster': 'testcluster',
          'id': 1,
          'jobrange': [1000, 2000],
          'other': {'notes': 0},
          'pain': 0.0,
          'resource': 'cpu',
          'resource_pretty': 'CPU',
          'state': 'pending',
          'state_pretty': 'Pending',
          'submitters': ['userQ'],
          'summary': None,
          'summary_pretty': '',
          'ticket': None,
          'ticket_id': None,
          'ticket_no': None,
          'ticks': 1
        }
      ]
    }
  }

@pytest.mark.dependency(name='bursts_posted')
def test_post_bursts(client, notifier):

  response = api_post(client, '/api/cases/', {
    'version': 2,
    'bursts': [
      {
        'account': 'def-dleske-aa',
        'resource': 'cpu',
        'pain': 1.0,
        'firstjob': 1005,
        'lastjob': 2005,
        'summary': None,
        'submitters': ['userQ']
      },
      {
        'account': 'def-bobaloo-aa',
        'resource': 'cpu',
        'pain': 1.5,
        'firstjob': 1015,
        'lastjob': 2015,
        'summary': None,
        'submitters': ['userQ']
      }
    ]})
  assert response.status_code == 201

  print(notifier.notifications)
  assert notifier.notifications == [
    'beam-dev: ReportReceived: bursts on testcluster: 0 new record(s) and 0 existing.  In total there are 0 pending, 0 accepted, 0 rejected.  0 have been claimed.',
    'beam-dev: ReportReceived: bursts on testcluster: 1 new record(s) and 0 existing.  In total there are 1 pending, 0 accepted, 0 rejected.  0 have been claimed.',
    "beam-dev: ReportReceived: bursts on testcluster: 2 new record(s) and 0 existing.  In total there are 2 pending, 0 accepted, 0 rejected.  0 have been claimed."]

@pytest.mark.dependency(depends=['bursts_posted'])
def test_get_bursts(client):

  response = api_get(client, '/api/cases/?report=bursts')
  assert response.status_code == 200
  x = json.loads(response.data)
  # TODO: test results!
  assert x is not None

def test_get_non_existent_burst(client):

  response = api_get(client, '/api/cases/11')
  assert response.status_code == 404

@pytest.mark.dependency(depends=['bursts_posted'])
def test_get_burst(client):

  response = api_get(client, '/api/cases/2')
  assert response.status_code == 200
  x = json.loads(response.data)
  del x['epoch']
  print(x)
  assert x == {
    'account': 'def-dleske-aa',
    'resource': 'cpu',
    'claimant': None,
    'cluster': 'testcluster',
    'id': 2,
    'jobrange': [1005, 2005],
    'pain': 1.0,
    'state': 'pending',
    'summary': None,
    'ticket_id': None,
    'ticket_no': None,
    'ticks': 1,
    'submitters': ['userQ'],
    'other': {'notes': 0}
  }

@pytest.mark.dependency(depends=['bursts_posted'])
def test_post_bursts_updated(client, notifier):

  # SQLite uses second-accuracy time so for consistency we do the same with
  # Postgres.  In testing we need to introduce a 1s delay to force the
  # following update to be of a different epoch than what we did above.
  time.sleep(1)

  response = api_post(client, '/api/cases/', {
    'version': 2,
    'bursts': [
      {
        'account': 'def-dleske-aa',
        'resource': 'cpu',
        'pain': 1.2,
        'firstjob': 1020,
        'lastjob': 2015,
        'summary': None,
        'submitters': ['userQ']
      }
    ]})
  assert response.status_code == 201

  assert notifier.notifications == [
    'beam-dev: ReportReceived: bursts on testcluster: 0 new record(s) and 0 existing.  In total there are 0 pending, 0 accepted, 0 rejected.  0 have been claimed.',
    'beam-dev: ReportReceived: bursts on testcluster: 1 new record(s) and 0 existing.  In total there are 1 pending, 0 accepted, 0 rejected.  0 have been claimed.',
    'beam-dev: ReportReceived: bursts on testcluster: 2 new record(s) and 0 existing.  In total there are 2 pending, 0 accepted, 0 rejected.  0 have been claimed.',
    'beam-dev: ReportReceived: bursts on testcluster: 0 new record(s) and 1 existing.  In total there are 1 pending, 0 accepted, 0 rejected.  0 have been claimed.']

  # now login and retrieve burst candidates as manager would
  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'admin1'})
  assert response.status_code == 302
  response = client.get('/xhr/cases/?cluster=testcluster')
  assert response.status_code == 200
  parsed = json.loads(response.data)
  print(parsed)

  # test we see what we should and not what we shouldn't
  assert parsed['cluster'] == 'testcluster'
  for burst in parsed['bursts']['results']:
    if burst['account'] == 'def-dleske-aa':
      # assert pain was updated
      assert burst['pain'] == 1.2

      # assert job range is updated correctly (range only extends upward)
      assert burst['jobrange'] == [1005,2015]
    else:
      # we should _not_ see the "bobaloo" account because it was in the
      # previous epoch and so no longer current
      assert burst['account'] != 'def-bobaloo-aa'

def test_post_bursts_with_updated_submitters(client, notifier):
  """
  Tests that submitters are updated correctly.
  """

  response = api_post(client, '/api/cases/', {
    'version': 2,
    'bursts': [
      {
        'account': 'def-dleske-aa',
        'resource': 'cpu',
        'pain': 1.0,
        'firstjob': 1005,
        'lastjob': 3000,
        'summary': None,
        'submitters': ['userQ']
      },
      {
        'account': 'def-bobaloo-aa',
        'resource': 'cpu',
        'pain': 1.5,
        'firstjob': 1015,
        'lastjob': 2015,
        'summary': None,
        'submitters': ['userX']
      }
    ]})
  assert response.status_code == 201

  assert notifier.notifications == [
    'beam-dev: ReportReceived: bursts on testcluster: 0 new record(s) and 0 existing.  In total there are 0 pending, 0 accepted, 0 rejected.  0 have been claimed.',
    'beam-dev: ReportReceived: bursts on testcluster: 1 new record(s) and 0 existing.  In total there are 1 pending, 0 accepted, 0 rejected.  0 have been claimed.',
    'beam-dev: ReportReceived: bursts on testcluster: 2 new record(s) and 0 existing.  In total there are 2 pending, 0 accepted, 0 rejected.  0 have been claimed.',
    'beam-dev: ReportReceived: bursts on testcluster: 0 new record(s) and 1 existing.  In total there are 1 pending, 0 accepted, 0 rejected.  0 have been claimed.',
    'beam-dev: ReportReceived: bursts on testcluster: 0 new record(s) and 2 existing.  In total there are 2 pending, 0 accepted, 0 rejected.  0 have been claimed.']

def test_post_bursts_with_other_updates(client, notifier):
  """
  Tests that state and claimant information in notification is correct.
  """

  id = 2
  data = [
    {
      'note': 'Hey how are ya',
      'datum': 'state',
      'value': 'rejected',
      'timestamp':'2019-03-31 10:31 AM'
    },
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
    'bursts': [
      {
        'account': 'def-dleske-aa',
        'resource': 'cpu',
        'pain': 1.0,
        'firstjob': 1005,
        'lastjob': 3000,
        'summary': None,
        'submitters': ['userQ']
      },
      {
        'account': 'def-bobaloo-aa',
        'resource': 'cpu',
        'pain': 1.5,
        'firstjob': 1015,
        'lastjob': 2015,
        'summary': None,
        'submitters': ['userQ']
      }
    ]})
  assert response.status_code == 201

  response = api_get(client, '/api/cases/{}'.format(id))
  print(json.loads(response.data))

  print(notifier.notifications)
  assert notifier.notifications[0] == \
    'beam-dev: ReportReceived: bursts on testcluster: 0 new record(s) and 0 existing.  In total there are 0 pending, 0 accepted, 0 rejected.  0 have been claimed.'
  assert notifier.notifications[1] == \
    'beam-dev: ReportReceived: bursts on testcluster: 1 new record(s) and 0 existing.  In total there are 1 pending, 0 accepted, 0 rejected.  0 have been claimed.'
  assert notifier.notifications[2] == \
    'beam-dev: ReportReceived: bursts on testcluster: 2 new record(s) and 0 existing.  In total there are 2 pending, 0 accepted, 0 rejected.  0 have been claimed.'
  assert notifier.notifications[3] == \
    'beam-dev: ReportReceived: bursts on testcluster: 0 new record(s) and 1 existing.  In total there are 1 pending, 0 accepted, 0 rejected.  0 have been claimed.'
  assert notifier.notifications[4] == \
    'beam-dev: ReportReceived: bursts on testcluster: 0 new record(s) and 2 existing.  In total there are 2 pending, 0 accepted, 0 rejected.  0 have been claimed.'
  assert notifier.notifications[5] == \
    'beam-dev: ReportReceived: bursts on testcluster: 0 new record(s) and 2 existing.  In total there are 1 pending, 0 accepted, 1 rejected.  1 have been claimed.'
