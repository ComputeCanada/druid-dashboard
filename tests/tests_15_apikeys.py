# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
import json
import pytest

# ---------------------------------------------------------------------------
#                                                                API KEYS
# ---------------------------------------------------------------------------

def test_get_apikeys_but_there_arent_any(client):

  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'admin1'})
  assert response.status_code == 302

  response = client.get('/xhr/apikeys/')
  assert response.status_code == 200
  assert json.loads(response.data) is None

@pytest.mark.dependency(name='apikeys_created')
def test_add_apikeys(client):

  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'admin1'})
  assert response.status_code == 302

  response = client.post('/xhr/apikeys/', data=dict(
    apikey_name='testapikey_d',
    apikey='WuHheVDysQQwdb+NK98w8EOHdiNUjLlz2Uxg/kIHqIGOek4DAmC5NCd2gZv7RQ==',
    component='testcluster_detector'
  ))
  assert response.status_code == 200

  response = client.post('/xhr/apikeys/', data=dict(
    apikey_name='testapikey_s',
    apikey='T3h5mwEk7mrVwxdon+s9blWhVh8zHDd7PVoUoWJsTf5Qd2EUie6I4pdBuyRykw==',
    component='testcluster_scheduler'
  ))
  assert response.status_code == 200

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
  assert response.status_code == 200

  response = client.post('/xhr/apikeys/', data=dict(
    apikey_name='testapikey2_s',
    apikey='GEMr1Ksi7I9G9BXuAhY4IITgMcyAKmHzgjFZ2uBTUpQkT1n3xUda5v+4FQAaBA==',
    component='testcluster2_scheduler'
  ))
  assert response.status_code == 200

  #response = client.post('/xhr/apikeys/', data=dict(
  #  apikey='gibberishdickensjustsuchweirdlycrap',
  #  apikey_name='different_key',
  #  component='testcluster_detector'
  #))
  #assert response.status_code == 200

@pytest.mark.dependency(depends=['apikeys_created'])
def test_get_apikeys(client):

  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'admin1'})
  assert response.status_code == 302

  response = client.get('/xhr/apikeys/')
  assert response.status_code == 200
  apikeys = json.loads(response.data)
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
     'component': 'Scheduler',
     'cluster': 'Test Cluster'
    },
    {'access': 'testapikey2_d',
     'component': 'Detector',
     'cluster': 'Test Cluster 2'
    },
    {'access': 'testapikey2_s',
     'component': 'Scheduler',
     'cluster': 'Test Cluster 2'
    }
  ], key=lambda x: x['access'])

@pytest.mark.dependency(depends=['apikeys_created'])
def test_delete_apikey_xhr(client):

  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'admin1'})
  assert response.status_code == 302

  response = client.delete('/xhr/apikeys/fakeyfakefake')
  assert response.status_code == 200

  response = client.get('/xhr/apikeys/')
  assert response.status_code == 200
  apikeys = json.loads(response.data)
  print(apikeys)
  assert sorted(apikeys, key=lambda x: x['access']) == sorted([
    #{'access': 'different_key',
    # 'component': 'Detector',
    # 'cluster': 'Test Cluster'
    #},
    {'access': 'testapikey_d',
     'component': 'Detector',
     'cluster': 'Test Cluster'
    },
    {'access': 'testapikey_s',
     'component': 'Scheduler',
     'cluster': 'Test Cluster'
    },
    {'access': 'testapikey2_d',
     'component': 'Detector',
     'cluster': 'Test Cluster 2'
    },
    {'access': 'testapikey2_s',
     'component': 'Scheduler',
     'cluster': 'Test Cluster 2'
    }
  ], key=lambda x: x['access'])
