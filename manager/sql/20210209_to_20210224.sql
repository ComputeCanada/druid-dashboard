DROP TABLE IF EXISTS burstsTMP;

-- create the temporary table matching the schema
CREATE TABLE burstsTMP (
  id INTEGER PRIMARY KEY,
  state CHAR(1) NOT NULL DEFAULT 'p',
  account VARCHAR(32) NOT NULL,
  cluster VARCHAR(16) NOT NULL,
  pain REAL NOT NULL,
  firstjob INTEGER NOT NULL,
  lastjob INTEGER NOT NULL,
  summary TEXT,
  epoch INTEGER NOT NULL,
  ticks INTEGER NOT NULL DEFAULT 0,
  claimant CHAR(7),
  CHECK (state in ('p', 'c', 'a', 'r')),
  FOREIGN KEY (cluster) REFERENCES clusters(id)
);

-- update the existing table to have a (n empty) column so there are enough
-- values to copy over in the next step
ALTER TABLE bursts ADD COLUMN claimant CHAR(7);

-- now copy everything over, get rid of the old, rename the new
INSERT INTO burstsTMP SELECT * FROM bursts;
DROP TABLE bursts;
ALTER TABLE burstsTMP RENAME TO bursts;

INSERT INTO schemalog (version, applied) VALUES ('20210224', CURRENT_TIMESTAMP);
