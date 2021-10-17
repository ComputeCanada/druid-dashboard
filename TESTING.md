# Testing

Insert clever pro-testing quotes here.

## Running tests

To activate the environment, issue the following from the root of the
repository, in one window (if you haven't yet set up the environment, see
[Setting up the development
environment](DEVELOPMENT.md#the-development-environment):

```
. venv/bin/activate
```

Automated testing is handled by a primary test script `tests/test-all`.  The
syntax help for this command is currently:

```
Usage: test-all [options]
Options:
  --no-sqlite:    Don't test SQLite (default to test SQLite)
  --pgsql:        Test Postgres
  --ldap:         Test LDAP integration
  --selenium:     Execute Selenium testing (default false)
  -a|--all:       Test all above if containers available
  --otrs:         Test OTRS integration.  Requires configuration file
                  tests/otrs.conf to exist (see sample).
  --no-cleanup:   Do not clean up temporary directories
  --schema:       Include schema upgrade testing
  --no-linting:   Skip lint testing
  --no-unit:      Skip unit testing
  -x|--exitfirst: [pytest] Exit at first failed test
  -v|--verbose:   [pytest] Show verbose information
  -d|--debug:     [pytest] Show debug-level logging

Postgres, LDAP and Selenium testing can only be performed if an appropriate
container is running with the label 'postgres-beam', 'ldap-beam', or
'selenium-beam', respectively.

OTRS testing *will create tickets and send e-mails*.  The tickets will be
automatically closed if successful, but e-mails will need to be verified
before cleanup.  OTRS testing is not included by `--all`.
```

Typical uses are described following.

### Essential tests

The default invocation starts with linting tests on Python and YAML files and
if successful continues with the 'essential' Python tests.  This test suite is
the basic one used most commonly during development--hence 'essential'.  This
uses SQLite and an LDAP stub.

```
$ tests/test-all
```

### Postgres integration

Once the above is functional, it is imperative we test against Postgres.  This
may surface issues in the differing schemas or in Postgres' more strictly
checking types and so on.

```
$ docker-compose -f tests/docker-pgsql.yml up -d
[...]
$ tests/test-all
[...]
$ docker-compose -f tests/docker-pgsql.yml down
```

### LDAP integration

Tests Postgres and LDAP.  One could skip the Postgres integration test and do
this one since it will also handle Postgres.

```
$ docker-compose -f tests/docker-ldap.yml up -d
[...]
$ tests/test-all
[...]
$ docker-compose -f tests/docker-ldap.yml down
```

### OTRS testing

OTRS testing exercises the templating and ticketing code and actually creates
a ticket on the configured test instance.  Tickets are automatically closed if
the tests succeed but the client and owner e-mails will need to be cleaned
up--they should be verified for correctness at this time.

OTRS testing should not be performed too frequently (to avoid too many test
tickets and testing spam).  It should probably be performed by the project
maintainer at their discretion.

### Selenium testing

Selenium testing simulates a browser and a user interacting with the
application.  To work the container must be up and running.  The Selenium test
suite also depends on the LDAP and Postgres containers being available.

```
$ docker-compose -f tests/docker-selenium up -d
$ tests/test-all --selenium
```

### The whole #!

```
$ tests/test-all --all
```

## Test coverage

Test coverage is printed out in a report at the end of execution:

```
---------- coverage: platform darwin, python 3.9.1-final-0 -----------
Name                        Stmts   Miss  Cover
-----------------------------------------------
manager/__init__.py           103      5    95%
manager/admin.py                8      0   100%
manager/ajax.py               264     98    63%
manager/api.py                133     21    84%
manager/apikey.py              76      8    89%
manager/auth.py                54      0   100%
manager/burst.py              153     20    87%
manager/case.py               245     39    84%
manager/cluster.py             34      1    97%
manager/component.py           81     21    74%
manager/dashboard.py           51     26    49%
manager/db.py                 151     66    56%
manager/db_postgres.py         39     39     0%
manager/db_sqlite.py           55      5    91%
manager/errors.py              42     17    60%
manager/event.py               59     13    78%
manager/exceptions.py          23      0   100%
manager/history.py             43      7    84%
manager/ldap.py                41     20    51%
manager/log.py                 13      1    92%
manager/notification.py        60     39    35%
manager/notifier.py            38      9    76%
manager/notifier_slack.py      32     20    38%
manager/oldjob.py              67      5    93%
manager/otrs.py                61     44    28%
manager/status.py              90     16    82%
manager/template.py            18      8    56%
-----------------------------------------------
TOTAL                        2034    548    73%
Coverage HTML written to dir htmlcov
```

The most important column is the `Miss` column, which shows the count of
executable lines not executed during the tests.

As can be seen, HTML output is also generated and available in the `htmlcov/`
directory.  This allows navigation from the index to individual files and
cleaerly marks off which lines are executed and which are missed, which is
useful for seeing where additional test cases need to be written.
