# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
import time
from email.utils import formatdate
import hmac
import base64
import json

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

def test_get_bursts(client):

  response = api_get(client, '/api/bursts')
  assert response.status_code == 200
  x = json.loads(response.data)
  assert x is not None

def test_get_burst(client):

  response = api_get(client, '/api/bursts/10')
  assert response.status_code == 200
  x = json.loads(response.data)
  print(x)
  assert x == {
    'account': 'def-ccc-aa',
    'resource': 'cpu',
    'claimant': None,
    'cluster': 'testcluster2',
    'epoch': 25,
    'id': 10,
    'jobrange': [17, 27],
    'pain': 2.5,
    'state': 'pending',
    'summary': None,
    'ticket_id': None,
    'ticket_no': None,
    'ticks': 0,
    'submitters': ['userQ']
  }

def test_post_nothing(client):

  response = api_post(client, '/api/bursts', {})
  assert response.status_code == 400
  assert response.data == b'{"error":"400 Bad Request: API violation: must define both \'version\' and \'bursts\'"}\n'

def test_post_burst_no_version(client):

  response = api_post(client, '/api/bursts', {
    'bursts': [
      {
        'account': 'def-dleske',
        'pain': 0.0,
        'firstjob': 1000,
        'lastjob': 2000,
        'summary': {}
      }
    ]})
  assert response.status_code == 400
  assert response.data == b'{"error":"400 Bad Request: API violation: must define both \'version\' and \'bursts\'"}\n'

def test_post_burst_old_version(client):
  # Note: version 0 of the API used "report" instead of "bursts", so using a
  # correct version 0 API call will trigger the wrong error response (in that
  # it's not the test response we want to test).
  response = api_post(client, '/api/bursts', {
    'version': 0,
    'bursts': [
      {
        'rapi': 'def-dleske',
        'pain': 0.0,
        'firstjob': 1000,
        'lastjob': 2000,
        'summary': {}
      }
    ]})

  expected = '{{"error":"400 Bad Request: Client API version (0) does not match server ({})"}}\n'.format(API_VERSION)

  assert response.status_code == 400
  assert response.data == expected.encode('utf-8')

def test_post_incomplete_burst_no_account(client):

  response = api_post(client, '/api/bursts', {
    'version': 1,
    'bursts': [
      {
        'resource': 'cpu',
        'pain': 0.0,
        'firstjob': 1000,
        'lastjob': 2000,
        'summary': {},
        'submitters': ['userQ']
      }
    ]})
  assert response.status_code == 400
  assert response.data == b'{"error":"400 Bad Request: Missing field required by API: \'account\'"}\n'

def test_post_incomplete_burst_no_firstjob(client):

  response = api_post(client, '/api/bursts', {
    'version': 1,
    'bursts': [
      {
        'account': 'def-dleske',
        'resource': 'cpu',
        'pain': 0.0,
        'lastjob': 2000,
        'summary': {},
        'submitters': ['userQ']
      }
    ]})
  assert response.status_code == 400
  assert response.data == b'{"error":"400 Bad Request: Missing field required by API: \'firstjob\'"}\n'

def test_post_incomplete_burst_no_lastjob(client):

  response = api_post(client, '/api/bursts', {
    'version': 1,
    'bursts': [
      {
        'account': 'def-dleske',
        'resource': 'cpu',
        'pain': 0.0,
        'firstjob': 1000,
        'summary': {},
        'submitters': ['userQ']
      }
    ]})
  assert response.status_code == 400
  assert response.data == b'{"error":"400 Bad Request: Missing field required by API: \'lastjob\'"}\n'

def test_post_incomplete_burst_no_pain(client):

  response = api_post(client, '/api/bursts', {
    'version': 1,
    'bursts': [
      {
        'account': 'def-dleske',
        'resource': 'cpu',
        'firstjob': 1000,
        'lastjob': 2000,
        'summary': {},
        'submitters': ['userQ']
      }
    ]})
  assert response.status_code == 400
  assert response.data == b'{"error":"400 Bad Request: Missing field required by API: \'pain\'"}\n'

def test_post_incomplete_burst_no_resource(client):

  response = api_post(client, '/api/bursts', {
    'version': 1,
    'bursts': [
      {
        'account': 'def-dleske',
        'pain': 0.0,
        'firstjob': 1000,
        'lastjob': 2000,
        'summary': {},
        'submitters': ['userQ']
      }
    ]})
  assert response.status_code == 400
  assert response.data == b'{"error":"400 Bad Request: Missing field required by API: \'resource\'"}\n'

def test_post_incomplete_burst_no_summary(client):

  response = api_post(client, '/api/bursts', {
    'version': 1,
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
  assert response.data == b'{"error":"400 Bad Request: Missing field required by API: \'summary\'"}\n'

def test_post_incomplete_burst_no_submitters(client):

  response = api_post(client, '/api/bursts', {
    'version': 1,
    'bursts': [
      {
        'account': 'def-dleske',
        'resource': 'cpu',
        'pain': 0.0,
        'firstjob': 1000,
        'lastjob': 2000,
        'summary': {}
      }
    ]})
  assert response.status_code == 400
  assert response.data == b'{"error":"400 Bad Request: Missing field required by API: \'submitters\'"}\n'

def test_post_bad_burst_bad_resource(client):

  response = api_post(client, '/api/bursts', {
    'version': 1,
    'bursts': [
      {
        'account': 'def-dleske',
        'resource': 'ppu',
        'pain': 0.0,
        'firstjob': 1000,
        'lastjob': 2000,
        'summary': {},
        'submitters': ['userQ']
      }
    ]})
  assert response.status_code == 400
  assert response.data == b'{"error":"400 Bad Request: Invalid resource type: \'ppu\'"}\n'

def test_post_empty_burst_report(client):
  """
  Tests that a report with no bursts is accepted as valid.
  """

  response = api_post(client, '/api/bursts', {
    'version': 1,
    'bursts': []
  })
  assert response.status_code == 201

def test_post_burst(client):

  response = api_post(client, '/api/bursts', {
    'version': 1,
    'bursts': [
      {
        'account': 'def-dleske',
        'resource': 'cpu',
        'pain': 0.0,
        'firstjob': 1000,
        'lastjob': 2000,
        'summary': {},
        'submitters': ['userQ']
      }
    ]})
  assert response.status_code == 201

def test_post_bursts(client):

  response = api_post(client, '/api/bursts', {
    'version': 1,
    'bursts': [
      {
        'account': 'def-dleske-aa',
        'resource': 'cpu',
        'pain': 1.0,
        'firstjob': 1005,
        'lastjob': 2005,
        'summary': {},
        'submitters': ['userQ']
      },
      {
        'account': 'def-bobaloo-aa',
        'resource': 'cpu',
        'pain': 1.5,
        'firstjob': 1015,
        'lastjob': 2015,
        'summary': {},
        'submitters': ['userQ']
      }
    ]})
  assert response.status_code == 201

  # SQLite uses second-accuracy time so for consistency we do the same with
  # Postgres.  In testing we need to introduce a 1s delay to force the
  # following update to be of a different epoch than what we did above.
  time.sleep(1)

  response = api_post(client, '/api/bursts', {
    'version': 1,
    'bursts': [
      {
        'account': 'def-dleske-aa',
        'resource': 'cpu',
        'pain': 1.2,
        'firstjob': 1020,
        'lastjob': 2015,
        'summary': {},
        'submitters': ['userQ']
      }
    ]})
  assert response.status_code == 201

  # now login and retrieve burst candidates as manager would
  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'admin1'})
  assert response.status_code == 302
  response = client.get('/xhr/bursts/')
  assert response.status_code == 200

  # test we see what we should and not what we shouldn't
  for burst in json.loads(response.data)['testcluster']['bursts']:
    if burst['account'] == 'def-dleske-aa':
      # assert pain was updated
      assert burst['pain'] == 1.2

      # assert job range is updated correctly (range only extends upward)
      assert burst['jobrange'] == [1005,2015]
    else:
      # we should _not_ see the "bobaloo" account because it was in the
      # previous epoch and so no longer current
      assert burst['account'] != 'def-bobaloo-aa'
