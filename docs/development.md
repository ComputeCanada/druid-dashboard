# Development

[[_TOC_]]

## Creating new report types

To create a new report type to be reported by a Detector to the Manager,
viewed on the Dashboard, subclass the Reporter class and implement the
necessary methods.  This will require additional code to handle the database
persistence and business logic related to the report.

### Database changes

You will define a new table to describe the data unique to your new report
type.  Much of the common information is handled by the base Reportables class
and its table: the cluster where the case was reported, the analyst that has
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
base class ("Reportable").  To this add the rest of the definitions you'll
need to track your case details.

The data definition for your new case type needs to be represented both in the
base schemas, used for populating an empty database, and the appropriate update
scriptage, used for updating an existing database to the latest schema
version.  The files are:

* `[manager/sql/schema.psql]` and `[manager/sql/schema.sql]`.  These are the
  base schemas for Postgres and SQLite, respectively.
* `[manager/sql/20210417_to_20210721.psql]` is the script that upgrades a
  database from schema version 20210417 to 20210721, for example.

The base schemas, defined for both SQLite and Postgres, are mostly identical
to eachother but differ in a few places, typically in the definition of the
auto-incrementing primary key, as well as `WITHOUT ROWID` for the SQLite
version, for the subclass tables whose primary key is the reportables' ID.

Every update to the base schema files requires an update to the schema
version.  This version must be the same in both the `.sql` and `.psql`
variants and must match what is in `[manager/db.py]`.  This is how the
application can tell it needs to execute the upgrade script.

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

(1) Prior data must be maintained, though of course it may well need to be
    transformed to another structure or transferred to another table.

(2) Remove any temporary tables created as part of the upgrade.

(3) Every upgrade script must finish by updating the database's schema
    version to what's in the updated schema and in the Python code.

#### Testing database upgrade

Testing a database upgrade before using it against a live database is
essential.  The best test is to make a copy of the live database and ensure:

(1) The upgrade script runs without errors or any unexpected results;
(2) The full test suite runs against the updated database.  This is not yet
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

#### Configuration items

Your new case module may require configuration items.  The `oldjob` module
does not; the `burst` module does, as it provides links to externally
generated usage graphs.  So in that case the URI template is configurable
rather than hardcoded in the module.

Configuration items are read from the environment or a configuration file, or
fall back to defaults defined in `__init__.py::defaults`.  If your new case
module requires configuration items:

(1) Define the configuration variable in `__init__.py` according to the
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
(2) When the app checks for configuration in the environment, it prepends its
    tag to the variable name before checking, to avoid naming conflicts.  So 
    the above example variable name would be defined in the environment as
    `BEAM_BURSTS_GRAPHS_INSTANT_URI`.
(3) In the configuration file, your module's configuration gets its own
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

You'll need to update [manager/__init__.py] to import the new Python module.

### UI updates

There is no current framework, as part of the dashboard application, for
augmenting the UI for new case types.  If this is what you need, open an issue
to start a discussion.

### Test cases

Create `tests/tests_yourcase.py` modeled after `tests/tests_oldjob.py` and
make appropriate changes.  Ensure test coverage registered by the tool is at
least 90% and that the only code missing in coverage is the exceptions.

