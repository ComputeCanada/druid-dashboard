# Testing

## Selenium testing

Selenium testing is always somewhat painful and/or laborious, or at least that
seems to be a common opinion.  There are two factors in this project and my
dev/test environment that complicates things a bit.  Actually quite a lot.

The first issue is the networking which is a result of the container setup I
have.  The containers are important as a way of both easily standing up and
also isolating various services, namely LDAP and Postgres.  There is also a
Nginx container for static resources which allows me to work in situations
where there's no external network.  As well, since all testing should be
reproducible in CI, Selenium itself is in a container so I don't have to
install stuff in my local workstation.

There is no problem with the networking between containers; the complications
arise when the containers need to talk to the host.  The containers can talk
to the host under a default Docker bridge network by addressing
`docker.host.internal`, but the host itself isn't aware of this address.  This
will become important later.

The second factor complicating the Selenium testing here is the use of
Selenium Wire, or specifically, the use of a proxy.  Selenium can't and won't
allow the injection of custom headers, which is required to test any operation
requiring an authenticated user, because authentication in this app depends on
authentication happening previously and the app receiving the authenticated
user's UID via a request header.  Selenium Wire offers a fairly easy drop-in
replacement for the Selenium `webdriver` module, but works by creating a proxy
on the local host for requests and responses to pass through and be captured
or manipulated.  This becomes a bit of a headache because of the above
networking.  Selenium (in a container) has to talk to Selenium Wire (on the
host) which must handle web requests sent by Selenium.

A third factor complicating testing is the integration of Pytest and a live
testing server.  Existing testing already had an app fixture that acted as a
server for running tests against, but Selenium, being a browser, requires an
actual web address.  (The `pytest_flask` module supports creation of a live
server but I could not get this to work properly; the routing seemed to break
down and while I could contact the server every request resulted in a 404.)  I
could fairly easily point Selenium at the development server but then every
test run would require me to manually stop, re-seed the database, and start
the server again, which could interfere with other development.  (Isolation is
beauty!)  So in the end: I created a server locally based on [borrowed
code](https://allanderek.github.io/posts/flask-and-pytest-coverage/) and this
handles setup and teardown and doesn't give me 404s on everything.

### Running Selenium tests locally with containers

This works on my development environment, which is a Python virtual
environment under Mac OS X.  It should work for other OSes but the use of the
alias `host.docker.internal` [_may_ not work under
Linux](https://stackoverflow.com/questions/48546124/what-is-linux-equivalent-of-host-docker-internal).

* Start up the LDAP, Postgres, static resources and Selenium containers with
  `docker compose -f tests/docker-selenium.yml up`.
* Set up an entry for the host `resources` to point to localhost.  This is
  because Selenium needs to get static resources from that container, but
  through Selenium Wire's proxy running on the host, which doesn't know what
  host "resources" is.  The host can see the resources container via
  `localhost:8080` but we can't use that with Selenium because then Selenium
  won't go through the proxy at all--and this will fail too.
* Ensure, as for all testing, the project's virtual Python environment is in
  place: `. venv/bin/activate`

Then start Selenium tests as follows:

```
$ BEAM_STATIC_RESOURCE_URI=http://resources:8080 \
    SELENIUM_URL=0.0.0.0:4444/wd/hub PYTHONPATH=. \
    pytest -v -x --log-level=debug tests/test_selenium.py
```
