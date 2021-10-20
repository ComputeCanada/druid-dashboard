# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=no-self-use
#
import json

# ---------------------------------------------------------------------------
#                                                COMPONENT MANAGEMENT TESTS
# ---------------------------------------------------------------------------

def test_get_no_components(empty_client):
  client = empty_client
  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'admin1'})
  print(response.status_code)
  assert response.status_code == 302

  response = client.get('/xhr/components/')
  assert response.status_code == 200
  print(response.data)
  assert json.loads(response.data) is None

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
     'name': 'Adjustor',
     'cluster': 'testcluster',
     'service': 'scheduler',
     'lastheard': None
    },
  ], key=lambda x: x['id'])

def test_delete_component_nonexistent(client):

  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'admin1'})
  assert response.status_code == 302

  response = client.delete('/xhr/components/testcluster_nonesuch')
  assert response.status_code == 404

  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'user1'})

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
     'name': 'Adjustor',
     'cluster': 'testcluster',
     'service': 'scheduler',
     'lastheard': None
    },
  ], key=lambda x: x['id'])

class TestComponentManagement:

  def test_create_components(self, client):

    response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'admin1'})

    response = client.post('/xhr/components/', data=dict(
      id='testcluster_scheduler2',
      name='Adjustor 2',
      cluster='testcluster',
      service='scheduler'
    ))
    assert response.status_code == 200

    response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'user1'})

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
       'name': 'Adjustor',
       'cluster': 'testcluster',
       'service': 'scheduler',
       'lastheard': None
      },
      {'id': 'testcluster_scheduler2',
       'name': 'Adjustor 2',
       'cluster': 'testcluster',
       'service': 'scheduler',
       'lastheard': None
      }
    ], key=lambda x: x['id'])

  def test_delete_component(self, client):

    response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'admin1'})
    assert response.status_code == 302

    response = client.delete('/xhr/components/testcluster_scheduler2')
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
       'name': 'Adjustor',
       'cluster': 'testcluster',
       'service': 'scheduler',
       'lastheard': None
      }
    ], key=lambda x: x['id'])
