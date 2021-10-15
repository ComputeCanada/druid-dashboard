# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=no-self-use
#
import json
from tests.tests_api import api_get

# ---------------------------------------------------------------------------
#                                                                API KEYS
# ---------------------------------------------------------------------------

def test_get_apikeys_but_there_arent_any(empty_client):

  response = empty_client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'admin1'})
  assert response.status_code == 302

  response = empty_client.get('/xhr/apikeys/')
  assert response.status_code == 200
  assert json.loads(response.data) is None

def test_add_apikey_with_bad_component(client):

  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'admin1'})
  assert response.status_code == 302

  response = client.post('/xhr/apikeys/', data=dict(
    apikey_name='no_apikey_here',
    apikey='rammarammadingdong',
    component='this_component_does_not_exist'
  ))
  assert response.status_code != 200

# use class to group the next few tests together since they build on
# eachother
class TestAPIKeyManagement:

  def test_add_apikeys(self, client):

    response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'admin1'})
    assert response.status_code == 302

    response = client.post('/xhr/apikeys/', data=dict(
      apikey_name='fakeyfakefake',
      apikey='ZoHCik4dOZm4VvKnkQUv9lcWydR8aH4bNCW2/fwxGGOfbj5SrBAY50nD3gNCIA==',
      component='testcluster_detector'
    ))
    assert response.status_code == 200

    response = client.post('/xhr/apikeys/', data=dict(
      apikey_name='testapikey2_d',
      apikey='rammarammadingdong',
      component='testcluster2_detector'
    ))
    assert response.status_code == 500

    response = client.post('/xhr/apikeys/', data=dict(
      apikey_name='testapikey2_s',
      apikey='GEMr1Ksi7I9G9BXuAhY4IITgMcyAKmHzgjFZ2uBTUpQkT1n3xUda5v+4FQAaBA==',
      component='testcluster2_scheduler'
    ))
    assert response.status_code == 500

  def test_get_apikeys(self, client):

    response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'admin1'})
    assert response.status_code == 302

    response = client.get('/xhr/apikeys/')
    assert response.status_code == 200
    apikeys = json.loads(response.data)
    print(apikeys)
    assert sorted(apikeys, key=lambda x: x['access']) == sorted([
      {'access': 'fakeyfakefake',
       'component': 'Detector',
       'cluster': 'Test Cluster'
      },
      {'access': 'testapikey_d',
       'component': 'Detector',
       'cluster': 'Test Cluster'
      },
      {'access': 'testapikey_s',
       'component': 'Adjustor',
       'cluster': 'Test Cluster'
      },
    ], key=lambda x: x['access'])

  def test_delete_apikey_xhr(self, client):

    response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'admin1'})
    assert response.status_code == 302

    response = client.delete('/xhr/apikeys/fakeyfakefake')
    assert response.status_code == 200

    response = client.get('/xhr/apikeys/')
    assert response.status_code == 200
    apikeys = json.loads(response.data)
    print(apikeys)
    assert sorted(apikeys, key=lambda x: x['access']) == sorted([
      {'access': 'testapikey_d',
       'component': 'Detector',
       'cluster': 'Test Cluster'
      },
      {'access': 'testapikey_s',
       'component': 'Adjustor',
       'cluster': 'Test Cluster'
      },
    ], key=lambda x: x['access'])

def test_get_components_lastheard(client):

  def sort(m):
    return sorted(m, key=lambda x: x['id'])

  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'admin1'})
  assert response.status_code == 302

  response = client.get('/xhr/components/')
  assert response.status_code == 200
  components = sort(json.loads(response.data))

  # for this test remember the lastheard value
  previous = components[0]['lastheard']

  # use API key to query API
  response = api_get(client, '/api/cases/?report=bursts&view=adjustor', access='testapikey_d',
    secret='WuHheVDysQQwdb+NK98w8EOHdiNUjLlz2Uxg/kIHqIGOek4DAmC5NCd2gZv7RQ==')
  assert response.status_code == 200

  # get components again
  response = client.get('/xhr/components/')
  assert response.status_code == 200
  components = sort(json.loads(response.data))

  # ensure lastheard was updated
  current = components[0]['lastheard']
  assert current != previous

  # just in case I guess
  del components[0]['lastheard']
  assert components[0] == {
    'id': 'testcluster_detector',
    'name': 'Detector',
    'cluster': 'testcluster',
    'service': 'detector'
    }
