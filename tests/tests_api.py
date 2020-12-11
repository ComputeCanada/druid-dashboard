# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
from email.utils import formatdate
import hmac
import base64
import json

def api_get(client, resource):

  # get current datestamp in RFC2822 format.  Without "localtime", will be
  # given a timezone of "-0000" which indicates, according to the RFC, that
  # nothing is known about the local time zone, offending the RFC (which
  # states that local time should be used) and resulting in a timezone-naive
  # RFC.  Yes, I'm annoyed how much time I spent figuring this out.
  date = formatdate(localtime=True)

  # build request string to digest
  digestible = "GET {}\n{}".format(resource, date)

  # test api key
  access = 'testapikey'
  secret = b'WuHheVDysQQwdb+NK98w8EOHdiNUjLlz2Uxg/kIHqIGOek4DAmC5NCd2gZv7RQ=='

  # create digest
  h = hmac.new(secret, digestmod='sha256')
  h.update(digestible.encode())
  digest = base64.b64encode(h.digest()).decode('utf-8')

  # headers to add to request
  headers = {
    'Date': date,
    'Authorization': "BEAM {} {}".format(access, digest)
  }

  return client.get(resource, headers=headers)


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
  assert x is None