/* We are adding a check here and SQLite doesn't support that sort of
 * alteration so we will destroy and recreate the table. */
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
  ticket_id INTEGER,
  ticket_no VARCHAR(9),
  resource CHAR(1) NOT NULL DEFAULT 'c',
  submitters TEXT NOT NULL,
  CHECK (state in ('p', 'c', 'a', 'r')),
  CHECK (resource in ('c', 'g')),
  FOREIGN KEY (cluster) REFERENCES clusters(id)
);

-- update the existing table to have a (n empty) column so there are enough
-- values to copy over in the next step
ALTER TABLE bursts ADD COLUMN resource CHAR(1) NOT NULL DEFAULT 'c';
ALTER TABLE bursts ADD COLUMN submitters TEXT NOT NULL DEFAULT '';

-- now copy everything over, get rid of the old, rename the new
INSERT INTO burstsTMP SELECT * FROM bursts;
DROP TABLE bursts;
ALTER TABLE burstsTMP RENAME TO bursts;

CREATE TABLE templates (
  name VARCHAR(32),
  language CHAR(2) NOT NULL DEFAULT '',
  content TEXT,
  PRIMARY KEY (name, language),
  CHECK (language IN ('', 'en', 'fr'))
);

INSERT INTO schemalog (version, applied) VALUES ('20210331', CURRENT_TIMESTAMP);
