# Development

[[_TOC_]]

## Developer setup

### Source code

```
# clone repository
git clone gitlab@git.computecanada.ca:frak/burst/manager.git
cd manager

# optional: checkout branch you want to base off of
#git checkout generalized-reports

# fetch submodules
git submodule update --init

# create virtual environment
python3 -m venv venv

# activate and install app and testing requirements
. venv/bin/activate
pip install -r requirements.txt
pip install -r tests/requirements.txt

# compile translations
pybabel compile -d manager/translations

# run essential tests
tests/test-all
```

The last step runs unit tests and the basic integration (using SQLite and
stubs for LDAP and other components).  These tests should all pass and you
should be ready to move on to the next step.

### Running application

If you are setting up your development instance for the first time, before
seeding your application with data, you will need to create the database
and load the schema. Please note that you will need the PSQL password to do
this. If you are using the included Docker container, you can find find the
password in tests/docker-pgsql.yml under POSTGRES_PASSWORD.

If you are using the included containers, you can start them with:
```
$ TAG=beam docker-compose -f tests/docker-ldap.yml up
```
This will bring up the necessary containers for a local development environment.
If you receive an error that the "bind source path does not exist.", create it using the following command:
```
mkdir instance/pg
```

Run the following command to create the database:
```
$ createdb -h localhost -p 5432 -U postgres beam_dev
```
You will need to enter the PSQL password, as outlined above.
Please note that the name of the database (shown here as beam_dev)
will need to match what is configured in manager.conf.

After the database has been created, you will need to import the schema.
You can do this using the following command. As before, you will be prompted
for your PSQL password.
```
$ psql -h localhost -p 5432 -U postgres -d beam_dev < manager/sql/schema.psql
```

We seed the database with some basic data (test cluster, register a detector
and adjustor for API calls, and associated API keys) and then start up the
server in development mode.  In development mode, more debug information is
displayed to the client and updated source triggers an automatic reload (on
the server side; the client browser may need to be refreshed).

```
# set up environment
export PYTHONPATH=$PYTHONPATH:.
export FLASK_APP=manager
export FLASK_ENV=development

# initialize and seed database with basic dev data
flask seed-db tests/dev.sql

# run application
flask run --with-threads
```

### Browser access

To use the application in your browser, you'll need to fake out the user
authentication.  When deployed the application runs behind a reverse proxy
which handles the single sign-on and, if the user authenticates successfully,
passes the authenticated username to the application using the
`X-Authenticated-User` header.

For Firefox, the [SimpleModifyHeaders
plugin](https://github.com/didierfred/SimpleModifyHeaders) works well enough.
Other browsers will require their own plugins unless they have an inbuilt
ability to add a header to every request.

Another possible option is running a small proxy locally to add the header.
The following [Tinyproxy](https://tinyproxy.github.io/) configuration works:

```
Port 5022
AddHeader "X-Authenticated-User" "admin1"
```

...for this Curl call:

```
$ curl -x localhost:5022 localhost:5001
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
<title>Redirecting...</title>
<h1>Redirecting...</h1>
<p>You should be redirected automatically to target URL: <a
href="/admin/">/admin/</a>.  If not click the link.
```

However Firefox does not funnel visits to localhost, 127.0.0.1, etc. through
configured proxies.

### Support containers

The LDAP instance is necessary in order to be able to look up user data.  A
Postgres container is necessary for testing against Postgres (which is a must
since deployment uses Postgres instead of SQLite).  A resources container
contains static resources such as third-party Javascript libraries.

To get these running, Docker must be installed and configured on your system.
It's recommended you run them in their own terminal so you can see activity.
To do so:

```
$ TAG=beam docker-compose -f tests/docker-ldap.yml up
```

Please note that you may need to log into the Compute Canada Git repository.
To do so:

```
$ docker login git.computecanada.ca:4567 --username yourUsernameHere
```

When prompted, please enter your access token with API access scope. 
If you do not have an Access Token, one can be created at: 
https://git.computecanada.ca/-/profile/personal_access_tokens

### App configuration

Put something like the following in `instance/manager.conf`:

```
[core]
static_resource_uri = http://localhost:8080
application_css_override = html{background:chartreuse}

[ldap]
# local testing
uri = ldap://localhost
# ONLY set the following for local testing!  Insecure!
skip_tls = yes
tls_reqcert = allow
```

The `application_css_override` is a simple trick to help differentiate your
local environment from the deployed one, by setting the background colour to
something obnoxious.

### Notifications

> Note: Notifications are not currently enabled.

To enable desktop notifications, you'll need a certificate for your
development server.  Generate this and put the cert and key in `instance/` and
invoke the Flask dev server with:

```
flask run --with-threads --cert instance/cert.pem --key instance/key.pem
```

## Translation

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

## Authentication and application credentials

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

## Replicating production database for development/upgrade testing

The databases used by the development and production instances of the BEAM
project contain potentially sensitive information and identifiers and should
not be distributed or added to source repositories.  That said, they represent
real data, are useful for development and testing, and are essential for
testing schema upgrades.

1. On *db.frak*, make a local backup of the `beam` database and globals:
    ```
    db.frak$ sudo su - postgres -c 'pg_dump -Fc  beam' > beam-schema-20210417.psql 
    db.frak$ sudo su - postgres -c 'pg_dumpall --globals-only -c' > beam-globals.psql
    ```
2. Copy those to the target workstation.  Then:
  * Ensure the globals (tablespaces and roles) are in place
  * Restore the given version of the database, in this case reflective of a
    particular schema version
  * Restore development API keys
    ```
    local$ psql -h localhost -U postgres < tests/beam-globals.psql
    local$ pg_restore -h localhost -U postgres -Cc -d postgres tests/beam-schema-20210417.psql
    local$ psql -h localhost -U postgres -d beam < tests/dev.sql
    ```

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

## Schema upgrade testing

See also [manager/sql/README.md](manager/sql/README.md).

Upgrading the schema may be performed one of two ways:

1. Upgrading manually from the command line.  This is recommended for initial
development.
    ```
    local$ psql -h localhost -U postgres < manager/sql/20210417_to_20210721.psql
    [ ... whatch for errors ... ]
    ```
2. Using the Manager, by visiting [the database upgrade URL](http://localhost:5001/status/db).

## Creating new report types

To create a new report type to be reported by a Detector to the Manager,
viewed on the Dashboard, subclass the Reporter class and implement the
necessary methods.  This will require additional code to handle the database
persistence and business logic related to the report.

What needs to be done:

* [ ] Create the database schema for the new subclass' table
  * [ ] Create a database upgrade script
  * [ ] Test the database upgrade script
* [ ] Create a subclass of the Case class
  * [ ] Implement required methods
  * [ ] Create any new configuration items as required
* [ ] Create additional actions
  * [ ] Add to `serialize()`
  * [ ] Write JavaScript handlers
* [ ] Create tests

### Database changes

You will define a new table to describe the data unique to your new report
type.  Much of the common information is handled by the base Case class and
its table: the cluster where the case was reported, the analyst that has
claimed the case for further investigation, and an associated ticket in OTRS,
if one has been created.  The new table will refer to this one and build on it
with new information.

The trivial case for the subclass's table is the following:
```
CREATE TABLE spacecases (
  id INTEGER PRIMARY KEY,
  FOREIGN KEY (id) REFERENCES reportables(id)
);
```

This creates a primary key which is a reference to the corresponding ID in the
base class ("Case").  To this add the rest of the definitions you'll need to
track your case details.

The data definition for your new case type needs to be represented both in the
base schemas, used for populating an empty database, and the appropriate update
scriptage, used for updating an existing database to the latest schema
version.  The files are:

* [manager/sql/schema.psql](manager/sql/schema.psql) and
* [manager/sql/schema.sql](manager/sql/schema.sql).  These are the
  base schemas for Postgres and SQLite, respectively.
* [manager/sql/20210417_to_20210721.psql](manager/sql/20210417_to_20210721.psql)
  is the script that upgrades a database from schema version 20210417 to
  20210721, for example.

The base schemas, defined for both SQLite and Postgres, are mostly identical
to eachother but differ in a few places, typically in the definition of the
auto-incrementing primary key, as well as `WITHOUT ROWID` for the SQLite
version, for the subclass tables whose primary key is the cases' ID.

Every update to the base schema files requires an update to the schema
version.  This version must be the same in both the `.sql` and `.psql`
variants and must match what is in [manager/db.py](manager/db.py).  This is
how the application can tell it needs to execute the upgrade script.

Things to remember in creating your schema:

* It needs to work for both SQLite and Postgres.  In most cases, the syntax
  will be identical, but not everywhere.
* Ensure you use `DROP TABLE IF EXISTS` for every new table.

#### Database upgrade scriptage

The upgrade scripts are more complex.  While the data definition language
between SQLite and Postgres are almost identical for _creating_ tables and so
on, the update language such as `ALTER TABLE` as well as some of the queries
can differ quite a bit.  Since the use of SQLite in this project is to
simplify the development environment (and it's a bit faster for testing), and
only Postgres is intended to be used for any deployment, there are no longer
upgrade scripts for SQLite.

So it simplifies things to require a single upgrade script.  However the
upgrade script must take a working database, make potentially complex updates
and in some cases manipulate data, and leave an upgraded _working_ database.

Use previous upgrade scripts as a helpful reference--but avoid the SQLite
versions, as their utility in writing upgrades for Postgres is pretty much
zero.

Things to watch out for in creating upgrade scripts:

1)  Prior data must be maintained, though of course it may well need to be
    transformed to another structure or transferred to another table.

2)  Remove any temporary tables created as part of the upgrade.

3)  Every upgrade script must finish by updating the database's schema
    version to what's in the updated schema and in the Python code.

#### Testing database upgrade

Testing a database upgrade before using it against a live database is
essential.  The best test is to make a copy of the live database and ensure:

1)  The upgrade script runs without errors or any unexpected results;
2)  The full test suite runs against the updated database.  This is not yet
    implemented (as of this writing the test suite builds up the database
    from scratch).

### Subclass `Case`

The Case class provides methods for reporting new cases, views into reported
cases, and represents the cases themselves.  Developers subclass the Case
class to define new reportable issues.

The [API documentation for the Case class](docs/case.md) describes the methods
that will need to be overridden in new subclasses, and existing Case types are
also available: `grep -lE 'class .*\(Case\):' manager/*`.  These subclasses
are both a reference and a checklist of methods that need to be overridden.

#### SQL queries

A new subclass will require several queries or query templates.  Existing Case
subclasses and method implementations provide examples.

There are no specific requirements but it is recommended that queries be
separated from the methods that use them and follow similar naming as existing
Case subclasses.

#### Configuration items

Your new case module may require configuration items.  The `oldjob` module
does not; the `burst` module does, as it provides links to externally
generated usage graphs.  So in that case the URI template is configurable
rather than hardcoded in the module.

Configuration items are read from the environment or a configuration file, or
fall back to defaults defined in `__init__.py::defaults`.  If your new case
module requires configuration items:

1)  Define the configuration variable in `__init__.py` according to the
    template `<CASENAME>_<VARNAME>`.
  * The case name should be the capitalized table name.
  * The variable name can be whatever makes sense for your module.
  * Break up multiple logical "words" with underscores and otherwise follow
    conventions set by other variables.
  * If there is no default value, set to an empty string.  If the default is
    not defined here, the app won't be aware of it and won't check the
    environment for it.  (When deployed to Kubernetes the app is configured
    primarily through environment variables.)
  * Example name: `BURSTS_GRAPHS_INSTANT_URI`
2)  When the app checks for configuration in the environment, it prepends its
    tag to the variable name before checking, to avoid naming conflicts.  So 
    the above example variable name would be defined in the environment as
    `BEAM_BURSTS_GRAPHS_INSTANT_URI`.
3)  In the configuration file, your module's configuration gets its own
    section.  Variable names match the above except the case name becomes the
    section name and everything is lowercase.  The above variable definition
    would be added to the configuration file as:
    ```
    [bursts]
    graphs_instant_uri = https://localhost/{cluster}/{account}_{resource}_instant.html
    ```

### Additional actions

Some case types might require additional actions.  For example, the burst
candidate workflow requires additional actions to handle candidate
state--whether the candidate has been accepted for bursting or rejected.

Additional actions are added in the `serialize()` method overridden by Case
subclasses.  To add two actions "Accept" and "Reject", one might use:

```
def serialize(self, pretty=False, options=None):
  # have superclass handle the basics
  serialized = super().serialize(
    pretty=pretty,
    options={'skip_summary_prettification': True}
  )

  # ...

  if pretty:
    serialized['actions'] = [
      {
        'id': 'reject',
        'label': _('Reject')
      },
      {
        'id': 'accept',
        'label': _('Accept')
      }
    ]

  return serialized
```

This will cause these choices to be added to the Action pulldown menu for each
case.  Additionally, handlers must be created on the client side to carry
these actions back to the server when chosen by the user.  For example, see
[the bursts state handlers](manager/static/bursts.js).

### API

To report a new type of case to the application, no updates to the API are
required.  When a report is posted to the API, the application uses the
report names to engage the appropriate class.

On the other hand, there is no general framework for retrieving some or all
cases from the API.  In the original Bursts use case, cases marked "Accepted"
are then retrievable via API to incorporate them into cluster scheduling, but
further currently envisioned case types have no such need.  If this is what
you need, open an issue to start a discussion.
 
### Other

You'll need to update [manager/__init__.py](manager/__init__.py) to import
the new Python module.

### UI updates

There is no current framework, as part of the dashboard application, for
augmenting the UI for new case types.  If this is what you need, open an issue
to start a discussion.

### Test cases

Create `tests/tests_yourcase.py` modeled after `tests/tests_oldjob.py` and
make appropriate changes.  Ensure test coverage registered by the tool is at
least 90% and that the only code missing in coverage is the exceptions.
