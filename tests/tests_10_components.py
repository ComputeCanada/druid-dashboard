# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
import json
import pytest

# ---------------------------------------------------------------------------
#                                                COMPONENT MANAGEMENT TESTS
# ---------------------------------------------------------------------------

def test_get_no_components(client):

  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'admin1'})
  assert response.status_code == 302

  response = client.get('/xhr/components/')
  assert response.status_code == 200
  print(response.data)
  assert json.loads(response.data) is None

@pytest.mark.dependency(name='components_created')
def test_create_components(client):

  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'admin1'})

  response = client.post('/xhr/components/', data=dict(
    name='Scheduler',
    cluster='testcluster',
    service='scheduler'
  ))
  assert response.status_code == 200

  response = client.post('/xhr/components/', data=dict(
    name='Detector',
    cluster='testcluster',
    service='detector'
  ))
  assert response.status_code == 200

@pytest.mark.dependency(depends=['components_created'])
def test_get_components(client):

  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'admin1'})

  response = client.get('/xhr/components/')
  assert response.status_code == 200
  components = json.loads(response.data)
  print(components)

  assert sorted(components, key=lambda x: x['id']) == sorted([
    {'id': 'testcluster_detector',
     'name': 'Detector',
     'cluster': 'testcluster',
     'service': 'detector',
     'lastheard': None
    },
    {'id': 'testcluster_scheduler',
     'name': 'Scheduler',
     'cluster': 'testcluster',
     'service': 'scheduler',
     'lastheard': None
    }
  ], key=lambda x: x['id'])

@pytest.mark.dependency(depends=['components_created'])
def test_delete_component_nonexistent(client):

  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'admin1'})
  assert response.status_code == 302

  response = client.delete('/xhr/components/testcluster_nonesuch')
  assert response.status_code == 404

  test_get_components(client)

@pytest.mark.dependency(depends=['components_created'], name='more_components_created')
def test_create_more_components(client):

  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'admin1'})

  response = client.post('/xhr/components/', data=dict(
    name='Scheduler',
    cluster='testcluster2',
    service='scheduler'
  ))
  assert response.status_code == 200
  assert json.loads(response.data) == {
    'status': 200,
  }

  response = client.post('/xhr/components/', data=dict(
    id='testcluster2_detector2',
    name='Detector 2',
    cluster='testcluster2',
    service='detector'
  ))

  assert response.status_code == 200
  response = client.post('/xhr/components/', data=dict(
    name='Detector',
    cluster='testcluster2',
    service='detector'
  ))
  assert response.status_code == 200

@pytest.mark.dependency(depends=['more_components_created'])
def test_delete_component(client):

  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'admin1'})
  assert response.status_code == 302

  response = client.delete('/xhr/components/testcluster2_detector2')
  assert response.status_code == 200

  response = client.get('/xhr/components/')
  assert response.status_code == 200
  components = json.loads(response.data)
  print(components)

  assert sorted(components, key=lambda x: x['id']) == sorted([
    {'id': 'testcluster_detector',
     'name': 'Detector',
     'cluster': 'testcluster',
     'service': 'detector',
     'lastheard': None
    },
    {'id': 'testcluster_scheduler',
     'name': 'Scheduler',
     'cluster': 'testcluster',
     'service': 'scheduler',
     'lastheard': None
    },
    {'id': 'testcluster2_detector',
     'name': 'Detector',
     'cluster': 'testcluster2',
     'service': 'detector',
     'lastheard': None
    },
    {'id': 'testcluster2_scheduler',
     'name': 'Scheduler',
     'cluster': 'testcluster2',
     'service': 'scheduler',
     'lastheard': None
    }
  ], key=lambda x: x['id'])
