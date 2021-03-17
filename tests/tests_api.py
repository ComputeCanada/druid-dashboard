# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
import time
from email.utils import formatdate
import hmac
import base64
import json

from manager.api import API_VERSION

def api_get(client, resource):

  # get current datestamp in RFC2822 format.  Without "localtime", will be
  # given a timezone of "-0000" which indicates, according to the RFC, that
  # nothing is known about the local time zone, offending the RFC (which
  # states that local time should be used) and resulting in a timezone-naive
  # RFC.  Yes, I'm annoyed how much time I spent figuring this out.
  timestamp = formatdate(localtime=True)

  # build request string to digest
  digestible = "GET {}\n{}".format(resource, timestamp)

  # test api key
  access = 'testapikey'
  secret = 'WuHheVDysQQwdb+NK98w8EOHdiNUjLlz2Uxg/kIHqIGOek4DAmC5NCd2gZv7RQ=='

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

  # test api key
  access = 'testapikey'
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
  assert x is None

def test_get_burst(client):

  response = api_get(client, '/api/bursts/10')
  assert response.status_code == 200
  x = json.loads(response.data)
  print(x)
  assert x == {
    'account': 'def-ccc-aa',
    'claimant': None,
    'cluster': 'testcluster2',
    'epoch': 25,
    'id': 10,
    'jobrange': [17, 27],
    'pain': 2.5,
    'state': 'p',
    'summary': None,
    'ticket_id': None,
    'ticket_no': None,
    'ticks': 0
  }

def test_post_burst_no_version(client):

  response = api_post(client, '/api/bursts', {
    'bursts': [
      {
        'account': 'def-dleske',
        'pain': 0.0,
        'firstjob': 1000,
        'lastjob': 2000
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
        'lastjob': 2000
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
        'pain': 0.0,
        'firstjob': 1000,
        'lastjob': 2000
      }
    ]})
  assert response.status_code == 400
  assert response.data == b'{"error":"400 Bad Request: Missing field required by API: \'account\'"}\n'

def test_post_incomplete_burst_no_summary(client):

  response = api_post(client, '/api/bursts', {
    'version': 1,
    'bursts': [
      {
        'account': 'def-dleske',
        'pain': 0.0,
        'firstjob': 1000,
        'lastjob': 2000
      }
    ]})
  assert response.status_code == 400
  assert response.data == b'{"error":"400 Bad Request: Missing field required by API: \'summary\'"}\n'

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
        'pain': 0.0,
        'firstjob': 1000,
        'lastjob': 2000,
        'summary': {}
      }
    ]})
  assert response.status_code == 201

def test_post_bursts(client):

  time.sleep(1)
  response = api_post(client, '/api/bursts', {
    'version': 1,
    'bursts': [
      {
        'account': 'def-dleske-aa',
        'pain': 1.0,
        'firstjob': 1005,
        'lastjob': 2005,
        'summary': {}
      },
      {
        'account': 'def-bobaloo-aa',
        'pain': 1.5,
        'firstjob': 1015,
        'lastjob': 2015,
        'summary': {}
      }
    ]})
  assert response.status_code == 201

  time.sleep(1)
  response = api_post(client, '/api/bursts', {
    'version': 1,
    'bursts': [
      {
        'account': 'def-dleske-aa',
        'pain': 1.2,
        'firstjob': 1020,
        'lastjob': 2015,
        'summary': {}
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
