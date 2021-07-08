# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
"""
Tests for miscellaneous AJAX calls.

This file contains testing for AJAX methods not covered by other test modules.
For example, burst-related AJAX calls are handled in tests_bursts.py along
with all the other burst stuff.
"""

import json
import pytest


# ---------------------------------------------------------------------------
#                                                  CLUSTER MANAGEMENT TESTS
# ---------------------------------------------------------------------------

def test_get_no_clusters(client):

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

@pytest.mark.dependency(name='clusters_created')
def test_create_clusters(client):

  # log in
  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'admin1'})

  response = client.post('/xhr/clusters/', data={
    'id': 'testcluster',
    'name': 'Test Cluster'
  })
  assert response.status_code == 201

  response = client.post('/xhr/clusters/', data={
    'id': 'testcluster2',
    'name': 'Test Cluster 2'
  })
  assert response.status_code == 201

@pytest.mark.dependency(depends=['clusters_created'])
def test_get_cluster(client):
  client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'user1'})

  response = client.get('/xhr/clusters/testcluster2')
  assert response.status_code == 200
  assert json.loads(response.data) == {
    'id': 'testcluster2',
    'name': 'Test Cluster 2'
  }

def test_get_cluster_no_exist(client):
  client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'user1'})

  response = client.get('/xhr/clusters/nosuchcluster')
  assert response.status_code == 404
  print(response.data)
  assert json.loads(response.data) == {
    'status': 404,
    'detail': 'Could not retrieve cluster "nosuchcluster"'
  }

# TODO: If I could mark this test as being dependent on starting with an
# unseeded database, I could use the rest of the tests on either a blank
# database or an existing one (such as a copy of the production database,
# for pre-upgrade testing)
#   Maybe "seeded" or "unseeded" will have to be set in a variable or some
# such.
#@pytest.mark.skipif(seeded)
@pytest.mark.dependency(depends=['clusters_created'])
def test_get_clusters(client):
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

@pytest.mark.dependency(depends=['clusters_created'])
def test_try_to_create_duplicate_cluster(client):

  # log in
  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'admin1'})

  response = client.post('/xhr/clusters/', data={
    'id': 'testcluster',
    'name': 'Test Cluster'
  })
  assert response.status_code == 400

  # re-run previous "get clusters", which should have the same again
  test_get_clusters(client)

# ---------------------------------------------------------------------------
#                                                COMPONENT MANAGEMENT TESTS
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
#                                                           TEMPLATES TESTS
# ---------------------------------------------------------------------------

@pytest.mark.dependency(depends=['bursts_created'])
def test_get_template(client):

  # log in
  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'user1'})
  assert response.status_code == 200

  # retrieve template
  response = client.get('/xhr/templates/impossible?burst_id=1')
  assert response.status_code == 200

  data = json.loads(response.data)
  assert data['title'] == "NOTICE: Your computations on Test Cluster may be optimized"
  print(data['body'])
  assert data['body'].startswith("""Hello PI 1,

Our records show that your account 'def-pi1' has a quantity of resources waiting in the job queue on Test Cluster which could experience substantial wait time. Upon inspection of your recent job history it has come to our attention that there may be job submission parameter changes which could alleviate the occurrence of these anticipated wait times.

If you would like to discuss this potential job submission parameter changes you can respond to this message and we will follow up with more details.

Best regards,

User 1
Compute Canada Support""")

# ---------------------------------------------------------------------------
#                                                                OTRS TESTS
# ---------------------------------------------------------------------------

def test_create_ticket_bad_call_xhr(client):

  # "log in"--normally user is logged in already when creating a ticket
  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'user1'})
  assert response.status_code == 200

  # post a create ticket request
  response = client.post('/xhr/tickets/', data={
    'burst_id': 1,
    'account': 'def-pi1',
  })
  assert response.status_code == 400

@pytest.mark.dependency(depends=['bursts_created'])
def test_create_ticket_xhr(client):
  """
  Use the OTRS Stub to ensure the ticket creation AJAX call sets up the
  correct templates and variables and that information is populated correctly.
  Does not actually (and should not) actually create a ticket in OTRS.  Doing
  so involves too much noise and potentially cleanup work outside of this
  project--deleting tickets, cleaning up test e-mail, etc.

  It may be valuable and reasonable in the future to create a test which
  executes as part of a suite that is only invoked manually and rarely--
  reproducible, yet more controlled.
  """

  # "log in"--normally user is logged in already when creating a ticket
  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'user1'})
  assert response.status_code == 200

  title = "NOTICE: Your computations on Test Cluster may be optimized"
  body = """Hello PI 1,

Our records show that your account 'def-pi1' has a quantity of resources waiting in the job queue on Test Cluster which could experience substantial wait time. Upon inspection of your recent job history it has come to our attention that there may be job submission parameter changes which could alleviate the occurrence of these anticipated wait times.

If you would like to discuss this potential job submission parameter changes you can respond to this message and we will follow up with more details.

Best regards,

User 1
Compute Canada Support"""

  # post a create ticket request
  response = client.post('/xhr/tickets/', data={
    'burst_id': 1,
    'title': title,
    'body': body,
    'recipient': 'pi1',
    'email': 'drew.leske+pi1@computecanada.ca'
  })
  assert response.status_code == 200

  x = json.loads(response.data)
  print(x)

  # pylint: disable=line-too-long
  assert x == {
    'burst_id': 1,
    'ticket_id': 1,
    'ticket_no': '01',
    'url': '/otrs/index.pl?Action=AgentTicketZoom&TicketID=1',
    'misc': {
      'ticket': {
        'CustomerUser': 'pi1',
        'Owner': 'user1',
        'Priority': '3 normal',
        'Queue': 'Test',
        'Responsible': 'user1',
        'State': 'new',
        'Title': 'NOTICE: Your computations on Test Cluster may be optimized'
        },
      'article': {
        'ArticleSend': 1,
        'ArticleType': 'email-external',
        'Body': "Hello PI 1,\n\nOur records show that your account 'def-pi1' has a quantity of resources waiting in the job queue on Test Cluster which could experience substantial wait time. Upon inspection of your recent job history it has come to our attention that there may be job submission parameter changes which could alleviate the occurrence of these anticipated wait times.\n\nIf you would like to discuss this potential job submission parameter changes you can respond to this message and we will follow up with more details.\n\nBest regards,\n\nUser 1\nCompute Canada Support",
        'Subject': 'NOTICE: Your computations on Test Cluster may be optimized',
        'To': 'drew.leske+pi1@computecanada.ca'
        },
      }
    }
