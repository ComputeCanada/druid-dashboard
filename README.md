# FRAK Burst Enablement - Burst Manager

A web application for managing bursts.

## Requirements

Python 3.8.
* Walrus operator (`:=` occuring in assignment expressions, allowing such as
  `if state := updates.get('state', None):`, for example)
* libraries imported from `requirements.txt`

## Architecture

This is implemented as a Flask app using LDAP and a database backend.

### LDAP

A [test LDAP container](https://git.computecanada.ca/dleske/ldap-ctnr)
provides test administrators, PIs and users as well as groups.  Authentication
is currently via database but usernames must match LDAP records; the intention
is to replace this with SSO authentication a level higher with credentials
delegated through to the app.

A [basic library for CC LDAP
access](https://git.computecanada.ca/dleske/python-ccldap) provides the
necessary functionality.

### Database

The database is SQLite for development and testing and Postgres for testing
and production.

### User interface

JQuery-UI provides tabs, dialog boxes and other UI elements.

## Setting up a development environment

### Git setup

First, clone the repository.  Then, you'll need the `tests` and `ccldap`
submodules.  These are defined in `.gitmodules` as _relative paths_ to ease
development and [enable
CI](https://docs.gitlab.com/ee/ci/git_submodules.html#using-git-submodules-in-your-ci-jobs).
The relative paths will cause you a bit of pain if you don't have your Git
workspaces set up in the same structure as on this GitLab instance, that is,
something like:

```
├── dleske
│   ├── python-ccldap
│   ├── tests
│   └── try-ldap-ctnr
├── frak
│   ├── burst
│   │   └── manager
│   └── smallest-asks-win
...
```

The first-level entries are the groups and the second-level are the projects.
So from `frak/burst/manager`, `../../../dleske/tests` takes you to the correct
project for the tests submodule.

If you don't replicate this structure, you can switch to using URLs, but if
you do so _do not push these changes_ as it will break CI.  Use the same
scheme you're currently using, presumably SSH:

```
[submodule "ccldap"]
        path = ccldap
        url = gitlab@git.computecanada.ca:dleske/python-ccldap.git
[submodule "tests/linting"]
        path = tests/linting
        url = gitlab@git.computecanada.ca:dleske/tests.git
```

To avoid seeing these local changes (which must remain local!) and pushing
them upstream inadvertently (because they must remain local!) use:

```
$ git update-index --skip-worktree  .gitmodules
```

Now to get the submodules:

```
$ git submodule update --init
```

### The development environment

Create and configure a virtual Python environment:

```
$ python3 -m venv venv
$ . venv/bin/activate
$ pip install -r requirements.txt
$ export PYTHONPATH=$PYTHONPATH:.
```

Setting `PYTHONPATH` is necessary for the module to be found.  If you know a
better way to handle this, let me know.

Set up some variables for running the Flask development server:

```
$ export FLASK_APP=manager
$ export FLASK_ENV=development
```

Now either initialize the DB with a schema or initialize it and seed it with
dev/test data:

```
$ flask init-db
```

Or

```
$ flask seed-db
```

### LDAP container

The LDAP instance is necessary in order to be able to look up user data.
The `tests/test-all-docker` script sets one up for testing and so contains the
necessary commands.  Setting up a separate container network is probably not
necessary for development so long as you specify the correct LDAP URI in your
application configuration.

### App configuration

Put something like the following in `instance/manager.conf`:
```
[ldap]
uri = ldap://localhost:3389
# only set this for testing!
skip_tls = yes
```

### Notifications

To enable desktop notifications, you'll need a certificate for your
development server.  Generate this and put the cert and key in `instance/` and
invoke the Flask dev server with:

```
flask run --with-threads --cert instance/cert.pem --key instance/key.pem
```

### Translation

> References:
>
> * [Flask:Babel home page](https://pythonhosted.org/Flask-Babel/)
> * [Flask Mega-Tutorial Part XIII](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xiii-i18n-and-l10n)

Use of i18n to support a French-language interface requires the following
steps (only needs to be done when adding new user-facing messages):

0. Mark any appropriate messages for translation using `_()` syntax:
    ```
    print(_('This used to be just English all the time!'))
    ```
   Look through the code for more complex examples, such as parametrized
   strings.
1. Extract text strings to translate:
    ```
    $ pybabel extract -F i18n/babel.cfg -k _l -o i18n/messages.pot .
    ```
2. Update the messages translation file with empty translations:
    ```
    $ pybabel update -i i18n/messages.pot -d manager/translations
    ```
3. Fill in the missing translations with your favourite editor.
4. Compile the messages:
    ```
    $ pybabel compile -d manager/translations
    ```

If I decide to replace the English strings in the Python source with static
"constants" (sigh, _Python_) then here'd be how to initialize that:

```
pybabel init -i messages.pot -d manager/translations -l en
```

## Testing

Testing includes linting, unit and integration tests, and Selenium tests.
Linting has no dependencies beyond having the correct software installed,
which should be the case for the virtual environment described above.

Unit and integration testing is described by `tests/test_unit.py` and requires
a database (set up by the fixtures in `tests/conftest.py`) and a test LDAP
instance.  This can be set up with `docker-compose -f tests/docker-compose.yml
up`.

Selenium testing simulates a web client and requires a separate service to be
run as well.  `tests/test-all-selenium` sets this up.  It is essentially a
superset of the previously mentioned test script because it covers
unit/integration testing as well.  (Requires `docker-compose`; `pip install
docker-compose` if not already present on your system.)

## API Access

API access is via an API key pair which must be used to create a digest of the
request, which is passed along with the request to be verified by the server.

### Creating an API key

If the Admin dashboard is unavailable for some other reason you want to do
this manually, here's how.

API keys are an arbitrary access string (read: username) and a 64-character
secret.  Secrets can be generated like so:

```
$ key=$(dd if=/dev/urandom bs=1 count=46 2>/dev/null | base64)
```

### Creating the request digest

The request digest is based on the request method, resource, and a timestamp,
in the following format:

```
$method $resource
$date
```

Example:

```
GET /api/widgets/current
Fri, 13 Dec 2019 20:35:01 +0000
```

The digest is created by hashing this summary with the secret key.  This can
be done in the shell like so:

```
echo -n $summary | openssl dgst -sha256 -hmac "$secret" -binary | base64
```

This digest must then be included as the `Authorization` HTTP header, _along
with a date header matching the same timestamp used in the digest_.

Putting these parts together, an API request can be accomplished with Curl as
follows (`access` and `secret` must be defined):

```
$ access="???"
$ secret="??????"
$ path=/api/widgets/current
$ date=$(date -Ru)
$ digest=$(echo -en "GET $path\n$date" | openssl dgst -sha256 -hmac "$secret" -binary | base64)
$ curl -H "Authorization: BEAM $access $digest" -H "Date: $date" localhost:5000${path}
```

A Python example can be found in `manager/apikey.py`.

## Logging

Various events and conditions result in log messages which are preferred over
`print()` statements (which should not exist in the code except for signalling
errors before the logging facility is available, or in temporary debugging).
The levels supported by the Python logging library, and how they are used in
this project, are as follows:

* `CRITICAL`: application broke and probably fell over.  (Sorry about that.)
* `ERROR`: the application has detected an inconsistency or some kind of
  condition causing an operation failure, although the application will
  continue.  This is potentially visible to the user and needs to be
  investigated.  If using this level, care should be taken to ensure the code
  handles cancellation of the failed operation such that data inconsistency is
  avoided.
* `WARNING`: an unexpected condition occurred but was handled and operation
  continued without adverse affect.  Investigation required to handle more
  robustly.
* `INFO`: informational notice.  This may include handled error conditions
  from client inputs such as failed authentications or useful information
  about the operation of the service.
* `DEBUG`: information useful for debugging and low-level diagnostics.

It would be appropriate to escalate messages of severity `WARNING` or higher.
`INFO` and `DEBUG` messages should provide value when using logs to diagnose
or investigate problems.

## Running tests

To set up the environment, issue the following from the root of the
repository, in one window:

### Unit tests

Uses SQLite and an LDAP stub.

```
$ tests/test-all
```

### Postgres integration

Tests Postgres as well, still using the LDAP stub.

```
$ docker-compose -f tests/docker-pgsql.yml up -d
[...]
$ tests/test-all
[...]
$ docker-compose -f tests/docker-pgsql.yml down
```

### LDAP integration

Tests Postgres and LDAP.

```
$ docker-compose -f tests/docker-ldap.yml up -d
[...]
$ tests/test-all
[...]
$ docker-compose -f tests/docker-ldap.yml down
```

## Development environment

### Authentication and application credentials

Authentication in this app assumes it is running behind a reverse proxy which
handles authentication and passes along the user in the HTTP request header
`X_AUTHENTICATED_USER`.  Without this you will get a 403, regardless of
which LDAP backend used (a real server, a local container, or a stub).  There
are two ways around this I'm aware of with Firefox.

1. Under Developer Tools, with the Network tab open, reload or visit the app.
Right-click on the 403 request for `/` or whatever path you entered and
selected *Edit and Resend*.  Add a header for `x-authenticated-user` set to
whichever user you want to fake out and click _Send_.  Note that this will
only work for one request.

2. Install a Firefox plugin to mangle headers for you.  I'm using
[SimpleModifyHeaders](https://github.com/didierfred/SimpleModifyHeaders/tree/v1.6.3).
