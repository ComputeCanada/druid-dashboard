# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
import json
from tests.tests_api import api_get

# ---------------------------------------------------------------------------
#                                                                COMPONENTS
# ---------------------------------------------------------------------------

def test_get_components_xhr(client):

  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'admin1'})
  assert response.status_code == 302

  response = client.get('/xhr/components/')
  assert response.status_code == 200
  components = json.loads(response.data)

  # for this test ignore the lastheard value
  del components[0]['lastheard']
  del components[1]['lastheard']
  del components[2]['lastheard']
  del components[3]['lastheard']

  assert sorted(components, key=lambda x: x['id']) == sorted([
    {'id': 'testcluster_detector',
     'name': 'Detector',
     'cluster': 'testcluster',
     'service': 'detector'
    },
    {'id': 'testcluster_scheduler',
     'name': 'Scheduler',
     'cluster': 'testcluster',
     'service': 'scheduler'
    },
    {'id': 'testcluster2_detector',
     'name': 'Detector',
     'cluster': 'testcluster2',
     'service': 'detector'
    },
    {'id': 'testcluster2_scheduler',
     'name': 'Scheduler',
     'cluster': 'testcluster2',
     'service': 'scheduler'
    }
  ], key=lambda x: x['id'])


def test_get_components_lastheard(client):

  def sort(m):
    return sorted(m, key=lambda x: x['id'])

  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'admin1'})
  assert response.status_code == 302

  response = client.get('/xhr/components/')
  assert response.status_code == 200
  components = sort(json.loads(response.data))

  # for this test remember the lastheard value
  previous = components[1]['lastheard']

  # use API key to query API
  response = api_get(client, '/api/bursts', access='testapikey2_s',
    secret='GEMr1Ksi7I9G9BXuAhY4IITgMcyAKmHzgjFZ2uBTUpQkT1n3xUda5v+4FQAaBA==')
  assert response.status_code == 200

  # get components again
  response = client.get('/xhr/components/')
  assert response.status_code == 200
  components = sort(json.loads(response.data))

  # ensure lastheard was updated
  current = components[1]['lastheard']
  assert current != previous

  # just in case I guess
  del components[1]['lastheard']
  assert components[1] == {
    'id': 'testcluster2_scheduler',
    'name': 'Scheduler',
    'cluster': 'testcluster2',
    'service': 'scheduler'
    }


# Need to create a cluster just for this and then add components
#def test_add_component_xhr(client):
#
#  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'admin1'})
#  assert response.status_code == 302
#
#  response = client.post('/xhr/components/', data=dict(
#    name='Test Cluster Scheduler',
#    cluster='testcluster',
#    service='scheduler'
#  ))
#  assert response.status_code == 200
#
#  response = client.get('/xhr/components/')
#  assert response.status_code == 200
#  components = json.loads(response.data)
#
#  del components[0]['lastheard']
#  assert sorted(components, key=lambda x: x['id']) == sorted([
#    {'id': 'testcluster_detector',
#     'name': 'Detector',
#     'cluster': 'testcluster',
#     'service': 'detector'
#    },
#    {'id': 'testcluster_scheduler',
#     'name': 'Test Cluster Scheduler',
#     'cluster': 'testcluster',
#     'service': 'scheduler',
#     'lastheard': None
#    }
#  ], key=lambda x: x['id'])
#
#def test_delete_component_xhr(client):
#
#  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'admin1'})
#  assert response.status_code == 302
#
#  response = client.delete('/xhr/components/testcluster_scheduler')
#  assert response.status_code == 200
#
#  response = client.get('/xhr/components/')
#  assert response.status_code == 200
#  components = json.loads(response.data)
#
#  del components[0]['lastheard']
#
#  assert sorted(components, key=lambda x: x['id']) == sorted([
#    {'id': 'testcluster_detector',
#     'name': 'Detector',
#     'cluster': 'testcluster',
#     'service': 'detector'
#    }
#  ], key=lambda x: x['id'])
