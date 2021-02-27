# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
# ---------------------------------------------------------------------------
#                                                                DASHBOARD
# ---------------------------------------------------------------------------

def test_dashboard(client):
  """
  GIVEN a Flask application
  WHEN  a correct user credential pair is provided to the login page
  THEN  the client will see the SAW dashboard
  """
  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'user1'})
  assert response.status_code == 200

  # check response data
  # just kidding


def test_basic_translation(client):
  """
  GIVEN a Flask application
  WHEN  an authenticated user requests French
  THEN  the client will see the SAW dashboard in French
  """
  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'user1'})
  response = client.get('/', environ_base={'HTTP_ACCEPT_LANGUAGE': 'fr'})
  assert b'Bonjour' in response.data
