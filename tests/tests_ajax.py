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

  # post a create ticket request
  response = client.post('/xhr/tickets/', data={
    'burst_id': 1,
    'account': 'def-pi1',
    'template': 'intro'
  })
  assert response.status_code == 200

  x = json.loads(response.data)
  print(x)

  # pylint: disable=line-too-long
  assert x == {
    'burst_id': 1,
    'ticket_id': 1,
    'ticket_no': '01',
    'misc': {
      'ticket': {
        'Title': 'NOTICE: Your computations may be eligible for prioritised execution',
        'Queue': 'Test',
        'State': 'new',
        'Priority': '3 normal',
        'CustomerUser': 'pi1',
        'Owner': 'user1',
        'Responsible': 'user1'
      },
      'article': {
        'Subject': 'NOTICE: Your computations may be eligible for prioritised execution',
        'Body': 'Hello PI 1,\n\nOngoing analysis of queued jobs on Test Cluster has shown that your project has a quantity of jobs that would benefit from a temporary escalation in priority.  Please let us know by replying to this message if you are interested.\n\nAdditional job info:\n  Current jobs: 1403\n  Submitters:   userQ\n\nBest regards,\nUser 1',
        'ArticleType': 'email-external',
        'ArticleSend': 1,
        'To': 'drew.leske+pi1@computecanada.ca'
      }
    },
    'url': '/otrs/index.pl?Action=AgentTicketZoom&TicketID=1'
  }

def test_create_ticket_multiplesubmitters_xhr(client):
  """
  See test_create_ticket_xhr.

  Tests that ticket and article are correctly filled out which in this case
  will require using multiple languages in article.
  """

  # "log in"--normally user is logged in already when creating a ticket
  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'user1'})
  assert response.status_code == 200

  # post a create ticket request
  response = client.post('/xhr/tickets/', data={
    'burst_id': 1,
    'account': 'def-pi1',
    'submitters': ['user3', 'user1'],
    'template': 'intro'
  })
  assert response.status_code == 200

  x = json.loads(response.data)
  print(x)

  # pylint: disable=line-too-long
  assert x == {
    'burst_id': 1,
    'ticket_id': 2,
    'ticket_no': '02',
    'misc': {
      'ticket': {
        'Title': 'NOTICE: Your computations may be eligible for prioritised execution / AVIS: Vos calculs peuvent être éligibles pour une exécution prioritaire',
        'Queue': 'Test',
        'State': 'new',
        'Priority': '3 normal',
        'CustomerUser': 'pi1',
        'Owner': 'user1',
        'Responsible': 'user1'
      },
      'article': {
        'Subject': 'NOTICE: Your computations may be eligible for prioritised execution / AVIS: Vos calculs peuvent être éligibles pour une exécution prioritaire',
        'Body': "\n(La version française de ce message suit.)\n\nHello PI 1,\n\nOngoing analysis of queued jobs on Test Cluster has shown that your project has a quantity of jobs that would benefit from a temporary escalation in priority.  Please let us know by replying to this message if you are interested.\n\nAdditional job info:\n  Current jobs: 1403\n  Submitters:   userQ\n\nBest regards,\nUser 1\n\n--------------------------------------\n\nBonjour PI 1,\n\nAnalyse en cours des travaux en attente sur Test Cluster a montré que votre projet comporte une quantité de tâches bénéficier d'une escalade temporaire en priorité. S'il vous plaît laissez-nous savoir par répondre à ce message si vous êtes intéressé.\n\nInfo additionel au tâches:\n  Tâches au courant:   1403\n  Emetteurs de tâches: userQ\n\nMeilleures salutations,\nUser 1",
        'ArticleType': 'email-external',
        'ArticleSend': 1,
        'To': 'drew.leske+pi1@computecanada.ca'
      }
    },
    'url': '/otrs/index.pl?Action=AgentTicketZoom&TicketID=2'
  }

# ---------------------------------------------------------------------------
#                                                              EVENTS TESTS
# ---------------------------------------------------------------------------

def test_create_note(client):
  """
  Create a note.
  """
  # log in
  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'user1'})
  assert response.status_code == 200

  # post a create note request
  response = client.post('/xhr/notes/', data={
    'burstID': 10,
    'analyst': 'xav-105',
    'text': 'First note',
    'timestamp': '2019-01-30 11:30:01 PDT'
  })

  assert response.status_code == 200
  x = json.loads(response.data)
  assert x['status'] == 'OK'

  response = client.post('/xhr/notes/', data={
    'burstID': 10,
    'analyst': 'xav-105',
    'text': 'Second note',
    'timestamp': '2019-02-27 13:30:31 PDT'
  })

  assert response.status_code == 200
  x = json.loads(response.data)
  assert x['status'] == 'OK'

  response = client.post('/xhr/notes/', data={
    'burstID': 10,
    'analyst': 'xav-105',
    'text': 'Between first and second note',
    'timestamp': '2019-02-14 13:30:31 PDT'
  })

  assert response.status_code == 200
  x = json.loads(response.data)
  assert x['status'] == 'OK'

def test_create_actions(client):
  """
  Create some actions.
  """
  # log in
  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'user1'})
  assert response.status_code == 200

  # post a create action request
  response = client.post('/xhr/actions/', data={
    'burstID': 10,
    'analyst': 'xav-105',
    'text': 'First action',
    'timestamp': '2019-01-30 11:33:01 PDT',
    'old_state': 'unclaimed',
    'new_state': 'claimed'
  })

  assert response.status_code == 200
  x = json.loads(response.data)
  assert x['status'] == 'OK'

  # post a create action request
  response = client.post('/xhr/actions/', data={
    'burstID': 10,
    'analyst': 'xav-105',
    'text': 'Second action',
    'timestamp': '2019-02-16 11:33:01 PDT',
    'old_state': 'unclaimed',
    'new_state': 'rejected'
  })

  assert response.status_code == 200
  x = json.loads(response.data)
  assert x['status'] == 'OK'


def test_get_events(client):
  """
  Get events related to a burst.
  """
  # log in
  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'user1'})
  assert response.status_code == 200

  # get events
  response = client.get('/xhr/events/?burstID=10')

  assert response.status_code == 200
  x = json.loads(response.data)
  del x[0]['id']
  del x[0]['timestamp']
  del x[1]['id']
  del x[1]['timestamp']
  del x[2]['id']
  del x[2]['timestamp']
  del x[3]['id']
  del x[3]['timestamp']
  del x[4]['id']
  del x[4]['timestamp']
  print(x)
  assert x == [
    {
      'burstID': 10,
      'analyst': 'xav-105',
      'text': 'First note'
    },
    {
      'burstID': 10,
      'analyst': 'xav-105',
      'text': 'First action',
      'old_state': 'unclaimed',
      'new_state': 'claimed'
    },
    {
      'burstID': 10,
      'analyst': 'xav-105',
      'text': 'Between first and second note'
    },
    {
      'burstID': 10,
      'analyst': 'xav-105',
      'text': 'Second action',
      'old_state': 'unclaimed',
      'new_state': 'rejected'
    },
    {
      'burstID': 10,
      'analyst': 'xav-105',
      'text': 'Second note'
    },
  ]
