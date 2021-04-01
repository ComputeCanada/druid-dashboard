# Database schema management

Schema files are tagged using lightweight tags of the format
`schema-<version>`.  Version is of the format `YYYYMMDD`.  Anytime a new
version is created, upgrade scripts from the previous version must be created.
These are named using the convention `<version>_to_<version>.<ext>` where
<ext> is appropriate to the database type (i.e. `sql` or `psql`).

Upgrade scripts consist of executable SQL statements, as are the schema files,
and should end with a line adding the appropriate version to the schema log:

```
INSERT INTO schemalog (version, applied) VALUES ('20210203', \
CURRENT_TIMESTAMP);
```

## Testing

Start at earliest schema, run upgrade to next schema, test that dump is
identical to next schema's, continue all the way along until latest.

This is not currently automated.

Older versions of the schema may be temporarily retrieved using `git show
schema-20201209:manager/sql/schema.sql`.  This may then be used to initialize
a development database and test upgrades.

## Changes to testing seed data

If the test suite's seed data changes (`/tests/data.sql`), an upgrade script
needs to be created for that as well, or upgrade testing will break, because
the upgrade testing is based on taking the seed data from a particular tag and
upgrading the database schema from there; without starting with seed data the
upgrade testing would only test updates to a blank database, which is not what
the upgrade or its testing is meant to accomplish.

Therefore, an upgrade script for the seed data must be created whenever the
seed data changes.  These must follow the filename convention
`/tests/data-YYYYMMDD.sql`.  These scripts are applied during upgrade
scripting in order along with the schema upgrade scripts and it is important
that data upgrade scripts are numbered so they are executed after the schema
update for which they apply.  If a schema upgrade and data upgrade script are
created on the same day, just name the data upgrade script for the next day.
