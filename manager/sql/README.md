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

If the test suite's seed data changes (`/tests/data.sql`), this will break
upgrade testing, because the upgrade testing currently is based on taking the
seed data from a particular tag and upgrading from there.  Since the seed
data's schema will be upgraded but the seed data won't be updated to reflect
the recent changes for the testing, the test suite based on the newer seed
data will fail.

(This could be worked around by including a file of updates to the seed data,
but the test suite would need to be updated to handle this and as well it is a
bunch of extra work that is probably not necessary.  For now I'll continue
with the idea below.)

When seed data is updated, a new "schema baseline" is established in the
`tests/test-all` script.  This implements a limit on schema upgrade testing to
that baseline and forward.  So if the baseline is set to 20210309 then only
versions newer than that will be tested for upgrades.

Obviously this requires previous versions' upgrades to be properly tested.

Schema version tagging as described above should be applied to the latest
commit of that with the schema updates and that with the updated seed data.
