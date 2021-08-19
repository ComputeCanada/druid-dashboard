# FRAK Burst Enablement - Burst Manager

A web application for managing bursts.

## Requirements

Python 3.6.
* libraries imported from `requirements.txt`

## Architecture

This is implemented as a Flask app using LDAP and a database backend.  The
application also connects to OTRS to create and manage tickets.

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

SQLite is more forgiving of syntax and structure and enables faster
prototyping and functional development.  Test suites also run noticeably
faster.

Postgres is a more robust platform with stricter syntax and type enforcement.
It's more suitable for deployment.

### User interface

The user interface is built on JavaScript, JQuery and
[Bootstrap 5](https://getbootstrap.com/docs/5.0/getting-started/introduction/).

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

For more information see [TESTING.md].

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
