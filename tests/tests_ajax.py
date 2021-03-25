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
        'Body': "Hello PI 1,\n\nOngoing analysis of queued jobs on TODO: TEST CLUSTER has shown that your project has a quantity of jobs that would benefit from a temporary escalation in priority.  Please let us know by replying to this message if you are interested.\n\nBest regards,\nUser 1",
        'ArticleType': 'email-external',
        'ArticleSend': 1,
        'To': 'drew.leske+pi1@computecanada.ca'
      }
    },
    'url': '/otrs/index.pl?TicketID=1'
  }
