# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=no-self-use
#
import json


# ---------------------------------------------------------------------------
#                                                  CLUSTER MANAGEMENT TESTS
# ---------------------------------------------------------------------------

def test_get_no_clusters(empty_client):
  client = empty_client
  # log in
  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'user1'})
  assert response.status_code == 200

  # get clusters
  response = client.get('/xhr/clusters/')
  assert response.status_code == 200
  print(response.data)
  assert json.loads(response.data) is None

def test_create_cluster_as_user_denied(client):

  # log in
  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'user1'})
  assert response.status_code == 200

  response = client.post('/xhr/clusters/', data={
    'id': 'testcluster',
    'name': 'Test Cluster'
  })
  assert response.status_code == 403

def test_get_clusters_seeded(client):
  client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'user1'})

  response = client.get('/xhr/clusters/')
  assert response.status_code == 200
  assert json.loads(response.data) == [
    {
      'id': 'testcluster',
      'name': 'Test Cluster'
    },
  ]

def test_get_cluster_no_exist(client):
  client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'user1'})

  response = client.get('/xhr/clusters/nosuchcluster')
  assert response.status_code == 404
  print(response.data)
  assert json.loads(response.data) == {
    'status': 404,
    'detail': 'Could not retrieve cluster "nosuchcluster"'
  }

class TestClusterManagement:

  def test_create_clusters(self, client):

    # log in
    response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'admin1'})

    response = client.post('/xhr/clusters/', data={
      'id': 'testcluster2',
      'name': 'Test Cluster 2'
    })
    assert response.status_code == 201

    response = client.get('/xhr/clusters/testcluster2')
    assert response.status_code == 200
    assert json.loads(response.data) == {
      'id': 'testcluster2',
      'name': 'Test Cluster 2'
    }

  def test_get_clusters(self, client):
    client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'user1'})

    response = client.get('/xhr/clusters/')
    assert response.status_code == 200
    assert json.loads(response.data) == [
      {
        'id': 'testcluster',
        'name': 'Test Cluster'
      },
      {
        'id': 'testcluster2',
        'name': 'Test Cluster 2'
      }
    ]

  def test_try_to_create_duplicate_cluster(self, client):

    # log in
    response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'admin1'})

    response = client.post('/xhr/clusters/', data={
      'id': 'testcluster',
      'name': 'Test Cluster'
    })
    assert response.status_code == 400

    # re-run previous "get clusters", which should have the same again
    self.test_get_clusters(client)
