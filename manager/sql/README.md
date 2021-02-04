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
