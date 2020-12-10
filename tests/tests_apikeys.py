# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
import json

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

  response = client.delete('/xhr/apikeys/fakeyfakefake')
  assert response.status_code == 200

  response = client.get('/xhr/apikeys/')
  assert response.status_code == 200
  apikeys = json.loads(response.data)
  assert sorted(apikeys) == [
    'different_key',
    'testapikey'
  ]
