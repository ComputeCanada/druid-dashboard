# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint: disable=W0621
#
# Selenium testing with own threaded test server
#
import os
import threading
from time import sleep
import tempfile
import wsgiref.simple_server
import pytest
from seleniumwire import webdriver
from tests.otrsstub import OtrsStub
from manager import create_app
from manager.db import get_db, init_db, seed_db

# address of container running selenium
selenium_url = os.environ.get('SELENIUM_URL', 'http://selenium:4444/wd/hub')

# address of proxy: this is so Selenium Remote driver can report back
# internal address is what Selenium Wire binds
selenium_proxy_internal = os.environ.get('SELENIUM_PROXY_INTERNAL', '127.0.0.1')
# this is how it'll be addressed by the remote web driver
selenium_proxy = os.environ.get('SELENIUM_PROXY', 'host.docker.internal')

# address and port of test server we'll start up.  We use 0.0.0.0 instead of
# localhost because the server needs to be externally available, for the
# containers
test_host = os.environ.get('TEST_HOST', '0.0.0.0')
test_port = os.environ.get('TEST_PORT', 60151)

# base application URL
app_url = "http://{}:{}".format(test_host, test_port)

# set up proxy.  Allow different ports so we have different clients for
# unauthenticated user, analyst, and admin.
def get_browser(port=8087):
  chrome_options = webdriver.ChromeOptions()
  chrome_options.add_argument('--proxy-server={}:{}'.format(selenium_proxy, port))
  chrome_options.add_argument('--headless')
  return webdriver.Remote(
    command_executor=selenium_url,
    desired_capabilities=chrome_options.to_capabilities(),
    seleniumwire_options={
      'auto_config': False,
      'addr': selenium_proxy_internal,
      'port': port
    }
  )

# threaded application server we setup and teardown just for this testing
class AppServer(threading.Thread):

  def __init__(self, app):
    self._httpd = wsgiref.simple_server.make_server(test_host, test_port, app)
    if not self._httpd:
      print("FAILED TO CREATE SERVER")
    super().__init__()

  def run(self):
    print("Starting up the server...")
    self._httpd.serve_forever()

  def stop(self):
    self._httpd.shutdown()
    self.join()

# ---------------------------------------------------------------------------
#                                                                  fixtures
# ---------------------------------------------------------------------------

# common test params; this was more useful when both SQLite and Postgres
# were handled in the same test setup module
test_params = [{
  'schema': 'schema.sql',
  'seed': '../tests/selenium-seed.sql',
  'delete_afterwards': True,
}]
test_ids = ['sqlite']

# seeded application fixture you may know from test suites such as
# test_sqlite.py
@pytest.fixture(scope='session', params=test_params, ids=test_ids)
def seeded_app(request):

  (filehandle, filename) = tempfile.mkstemp()
  uri = 'file://' + filename

  app = create_app({
    'TESTING': True,
    'DATABASE_URI': uri,
    'CONFIG': 'tests/app.conf',
    'OTRS_STUB': OtrsStub(),
    'STATIC_RESOURCE_URI': 'http://resources'
  })

  with app.app_context():
    init_db()
    seed_db(request.param['seed'])
    get_db().commit()

  yield app

  if request.param.get('delete_afterwards', False):
    os.close(filehandle)
    os.unlink(filename)

@pytest.fixture(scope='session')
def server(seeded_app):
  testserver = AppServer(seeded_app)
  testserver.start()
  yield
  testserver.stop()

@pytest.fixture(scope='session')
def anon(server):
  # pylint: disable=unused-argument
  browser = get_browser()
  yield browser
  browser.quit()

def admin_authenticator(request):
  request.headers['x-authenticated-user'] = 'dleske'

@pytest.fixture(scope='session')
def admin(server):
  # pylint: disable=unused-argument
  browser = get_browser(8088)
  browser.request_interceptor = admin_authenticator
  yield browser
  browser.quit()

def analyst_authenticator(request):
  request.headers['x-authenticated-user'] = 'user1'

@pytest.fixture(scope='session')
def analyst(server):
  # pylint: disable=unused-argument
  browser = get_browser(8089)
  browser.request_interceptor = analyst_authenticator
  yield browser
  browser.quit()

# ---------------------------------------------------------------------------
#                                                                     tests
# ---------------------------------------------------------------------------

def test_access_denied(anon):
  anon.get(app_url)
  print("Browser URL: " + anon.current_url)
  print(anon.title)
  assert "Burst Enablement" in anon.title
  assert "Access forbidden" in anon.title

def test_status(anon):
  anon.get(app_url + '/status')
  print(anon.page_source)
  assert "I'm: Okay" in anon.page_source

def test_analyst_login_initial(analyst):
  analyst.get(app_url)

  assert "Burst Enablement" in analyst.title
  assert "Dashboard" in analyst.title
  assert "Hello, Drew" not in analyst.page_source
  assert "Hello, User 1" in analyst.page_source

def test_admin_landing(admin):

  admin.get(app_url)
  print(admin.current_url)
  print(admin.title)
  assert "Burst Enablement" in admin.title

  # this is an admin
  assert "Admin" in admin.title
  assert (app_url + '/admin/') == admin.current_url

def test_admin_to_dashboard(admin):

  admin.get(app_url)

  # this is an admin, so switch to user view
  dashboard_link = admin.find_element_by_link_text('Switch to user view')
  dashboard_link.click()

  print(admin.requests)

  assert "Dashboard" in admin.title

  admin.set_window_size(1200,800)
  #admin.get_screenshot_as_file('screenshot_dashboard_admin.png')

def test_admin_stays_in_dashboard(admin):

  # admin user should return to dashboard--assuming cookie set properly
  admin.get(app_url)
  assert "Dashboard" in admin.title

def test_analyst_login(analyst):

  analyst.get(app_url)
  assert "Burst Enablement" in analyst.title
  assert "Dashboard" in analyst.title
  assert "Hello, Drew" not in analyst.page_source
  assert "Hello, User 1" in analyst.page_source

def test_actionmenu_button(analyst):

  analyst.set_window_size(1200,800)
  del analyst.requests
  analyst.get(app_url)
  for request in analyst.requests:
    if request.response:
      print(
        request.url,
        request.response.status_code,
        request.response.headers['Content-Type']
      )
  sleep(0.5)
  analyst.get_screenshot_as_file('screenshot.png')

  action_button = analyst.find_element_by_id('actionMenuButton_4')
  action_button.click()
  action_history_button = analyst.find_element_by_id('action_history_4')
  action_history_button.click()

  sleep(0.5)
  historyModalBody = analyst.find_element_by_id('historyModalBody')
  print(historyModalBody.text)
  assert historyModalBody.text == "No events recorded for this burst candidate."
  mkay_button = analyst.find_element_by_id('history_mkay')
  mkay_button.click()

  action_button.click()
  action_note_button = analyst.find_element_by_id('action_note_4')
  action_note_button.click()

  sleep(0.5)
  note_textarea = analyst.find_element_by_id('noteModalTextarea')
  note_textarea.send_keys("""This user is requesting more memory than suitable
for this type of job.

Will follow up.""")
  submit_button = analyst.find_element_by_id('noteModalSubmit')
  submit_button.click()

  sleep(0.5)
  action_button = analyst.find_element_by_id('actionMenuButton_4')
  action_button.click()
  action_history_button = analyst.find_element_by_id('action_history_4')
  action_history_button.click()

  sleep(0.5)
  historyModalBody = analyst.find_element_by_id('historyModalBody')
  assert "This user is requesting more memory than suitable" in historyModalBody.text
  assert "Will follow up." in historyModalBody.text
  mkay_button = analyst.find_element_by_id('history_mkay')
  mkay_button.click()
