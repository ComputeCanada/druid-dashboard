# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
#import logging
import hmac
import base64
from email.utils import formatdate
import json
import pytest
from app import create_app
from app.db import init_db, SCHEMA_VERSION
import app.exceptions

# ---------------------------------------------------------------------------
#                                                          APP
# ---------------------------------------------------------------------------

def test_config():
  assert not create_app().testing
  assert create_app({'TESTING': True}).testing


def test_config_bad_database():
  beam = create_app({'DATABASE_URI': 'stupid://does.not.work:666/goodbye'})
  assert beam
  with beam.app_context():
    with pytest.raises(app.exceptions.UnsupportedDatabase) as e:
      init_db()
  assert e.value.scheme == 'stupid'
  assert str(e.value) == "Unsupported database type/scheme: stupid"

# ---------------------------------------------------------------------------
#                                                             AUTHENTICATION
# ---------------------------------------------------------------------------

def test_delegated_credential(client):
  """
  GIVEN a Flask application
  WHEN  a username is set in the environment
  THEN  the client will authenticate that username
  """
  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'pi1'})
  assert response.status_code == 200
  assert b'Hello, PI 1' in response.data


def test_user_missing_attributes(client):
  """
  WHEN user has fewer than all required attributes
  THEN the authorization fails
  """
  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'user2'})
  assert response.status_code == 403


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
    'Authorization': "SAW {} {}".format(access, digest)
  }

  return client.get(resource, headers=headers)


def test_admin_redirect(client):
  """
  GIVEN a Flask application
  WHEN  a correct admin credential identifier is provided
  THEN  the client is logged in and redirected to the admin dashboard
  """
  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'admin1'})
  assert response.status_code == 302
  assert b'You should be redirected automatically to target URL: <a href="/admin/">/admin/</a>' in response.data


def test_admin_view_mode(client):
  """
  GIVEN a Flask application
  WHEN  a correct admin credential identifier is provided and mode is set in query
  THEN  the client is redirected as appropriate for the mode
  """
  response = client.get('/?mode=user', environ_base={'HTTP_X_AUTHENTICATED_USER': 'admin1'})
  assert response.status_code == 200
  assert b'Switch to admin view' in response.data

  response = client.get('/?mode=admin', environ_base={'HTTP_X_AUTHENTICATED_USER': 'admin1'})
  assert response.status_code == 302
  assert b'You should be redirected automatically to target URL: <a href="/admin/">/admin/</a>' in response.data


def test_failed_login_bad_user(client):
  """
  GIVEN a Flask application
  WHEN  an invalid user ID is provided to the application
  THEN  the client will get a 403
  """
  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'DonaldJTrump'})
  assert response.status_code == 403


# ---------------------------------------------------------------------------
#                                                                STATUS
# ---------------------------------------------------------------------------

def test_status(client):
  """
  Test that /status returns a 200 in the case of things working, which they
  should be here because it's stubbed out.
  """
  response = client.get('/status/')
  assert response.status_code == 200
  assert response.data == 'LDAP: Okay\nDB: Okay (schema version {})'.format(SCHEMA_VERSION).encode('utf-8')

# ---------------------------------------------------------------------------
#                                                                DASHBOARD
# ---------------------------------------------------------------------------

def test_dashboard(client):
  """
  GIVEN a Flask application
  WHEN  a correct user credential pair is provided to the login page
  THEN  the client will see the SAW dashboard
  """
  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'pi1'})
  assert response.status_code == 200

  # check response data
  # just kidding

def test_basic_translation(client):
  """
  GIVEN a Flask application
  WHEN  an authenticated user requests French
  THEN  the client will see the SAW dashboard in French
  """
  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'pi1'})
  response = client.get('/', environ_base={'HTTP_ACCEPT_LANGUAGE': 'fr'})
  assert b'Bonjour' in response.data


# ---------------------------------------------------------------------------
#                                                                API KEYS
# ---------------------------------------------------------------------------

def test_get_apikeys_xhr(client):

  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'admin1'})
  assert response.status_code == 302

  response = client.get('/xhr/apikeys/')
  assert response.status_code == 200
  apikeys = json.loads(response.data)
  assert sorted(apikeys) == [
    'fakeyfakefake',
    'testapikey'
  ]

def test_add_apikey_xhr(client):

  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'admin1'})
  assert response.status_code == 302

  response = client.post('/xhr/apikeys/', data=dict(
    apikey='gibberishdickensjustsuchweirdlycrap',
    apikey_name='different_key'
  ))
  assert response.status_code == 200

  response = client.get('/xhr/apikeys/')
  assert response.status_code == 200
  apikeys = json.loads(response.data)
  assert sorted(apikeys) == [
    'different_key',
    'fakeyfakefake',
    'testapikey'
  ]

def test_delete_apikey_xhr(client):

  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'admin1'})
  assert response.status_code == 302

  response = client.delete('/xhr/apikeys/testapikey')
  assert response.status_code == 200

  response = client.get('/xhr/apikeys/')
  assert response.status_code == 200
  apikeys = json.loads(response.data)
  assert sorted(apikeys) == [
    'different_key',
    'fakeyfakefake'
  ]
