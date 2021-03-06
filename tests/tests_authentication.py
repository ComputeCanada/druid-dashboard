# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
# ---------------------------------------------------------------------------
#                                                             AUTHENTICATION
# ---------------------------------------------------------------------------

def test_delegated_credential(client):
  """
  GIVEN a Flask application
  WHEN  a username is set in the environment
  THEN  the client will authenticate that username
  """
  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'user1'})
  assert response.status_code == 200
  assert b'Hello, User 1' in response.data


def test_user_missing_attributes(client):
  """
  WHEN user has fewer than all required attributes
  THEN the authorization fails
  """
  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'user2'})
  assert response.status_code == 403


def test_user_denied(client):
  """
  GIVEN a Flask application
  WHEN  a correct user credential identifier is provided but one without
        analyst privileges tries to access the dashboard
  THEN  the client is denied
  """
  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'user3'})
  assert response.status_code == 403


def test_admin_denied(client):
  """
  GIVEN a Flask application
  WHEN  a correct user credential identifier is provided but one without admin
        privileges tries to access the admin dashboard
  THEN  the client is denied
  """
  response = client.get('/admin/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'user1'})
  assert response.status_code == 403


def test_admin_redirect(client):
  """
  GIVEN a Flask application
  WHEN  a correct admin credential identifier is provided
  THEN  the client is logged in and redirected to the admin dashboard
  """
  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'admin1'})
  assert response.status_code == 302
  assert b'You should be redirected automatically to target URL: <a href="/admin/">/admin/</a>' in response.data


def test_admin_view_mode(client):
  """
  GIVEN a Flask application
  WHEN  a correct admin credential identifier is provided and mode is set in query
  THEN  the client is redirected as appropriate for the mode
  """
  response = client.get('/user', environ_base={'HTTP_X_AUTHENTICATED_USER': 'admin1'})
  assert response.status_code == 302
  assert b'You should be redirected automatically to target URL: <a href="/">/</a>' in response.data

  response = client.get('/admin/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'admin1'})
  assert response.status_code == 200
  assert b'Switch to user view' in response.data


def test_failed_login_bad_user(client):
  """
  GIVEN a Flask application
  WHEN  an invalid user ID is provided to the application
  THEN  the client will get a 403
  """
  response = client.get('/', environ_base={'HTTP_X_AUTHENTICATED_USER': 'DonaldJTrump'})
  assert response.status_code == 403
