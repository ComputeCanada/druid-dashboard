/* We are adding a check here and SQLite doesn't support that sort of
 * alteration so we will destroy and recreate the table. */
DROP TABLE IF EXISTS burstsTMP;

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
  CHECK (state in ('p', 'a', 'r')),
  CHECK (resource in ('c', 'g')),
  FOREIGN KEY (cluster) REFERENCES clusters(id)
);

-- update the existing table to have not use 'c' state (update to 'p')
UPDATE bursts SET state='p' WHERE state='c';

-- now copy everything over, get rid of the old, rename the new
-- need to specify rows explicitly to avoid column ordering issues
INSERT INTO burstsTMP SELECT id, state, account, cluster, pain, firstjob,
  lastjob, summary, epoch, ticks, claimant, ticket_id, ticket_no, resource,
  submitters FROM bursts;
DROP TABLE bursts;
ALTER TABLE burstsTMP RENAME TO bursts;

CREATE TABLE notes (
  id INTEGER PRIMARY KEY,
  burst_id INTEGER NOT NULL,
  analyst CHAR(7),
  timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  note TEXT,
  FOREIGN KEY (burst_id) REFERENCES bursts(id)
);

CREATE TABLE updates_state (
  id INTEGER PRIMARY KEY,
  burst_id INTEGER NOT NULL,
  analyst CHAR(7),
  timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  note TEXT,
  old_state CHAR(1),
  new_state CHAR(1),
  FOREIGN KEY (burst_id) REFERENCES bursts(id),
  CHECK (old_state in ('p', 'a', 'r')),
  CHECK (new_state in ('p', 'a', 'r'))
);

CREATE TABLE updates_claimant (
  id INTEGER PRIMARY KEY,
  burst_id INTEGER NOT NULL,
  analyst CHAR(7),
  timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  note TEXT,
  claimant_was CHAR(7),
  claimant_now CHAR(7),
  FOREIGN KEY (burst_id) REFERENCES bursts(id)
);

INSERT INTO schemalog (version, applied) VALUES ('20210417', CURRENT_TIMESTAMP);
