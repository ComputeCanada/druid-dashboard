DROP TABLE IF EXISTS schemalog;
DROP TABLE IF EXISTS apikeys;
DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS components;
DROP TABLE IF EXISTS notes;
DROP TABLE IF EXISTS bursts;
DROP TABLE IF EXISTS clusters;
DROP TABLE IF EXISTS notifiers;
DROP TABLE IF EXISTS templates;
DROP TABLE IF EXISTS job_ages;
DROP TABLE IF EXISTS reportables;
DROP TABLE IF EXISTS history;

CREATE TABLE schemalog (
  version VARCHAR(10) PRIMARY KEY,
  applied TIMESTAMP
);
INSERT INTO schemalog (version, applied) VALUES ('20210721', CURRENT_TIMESTAMP);

CREATE TABLE clusters (
  id VARCHAR(16) UNIQUE NOT NULL,
  name VARCHAR(32) UNIQUE NOT NULL
);

CREATE TABLE components (
  id VARCHAR(32) UNIQUE NOT NULL,
  name VARCHAR(64) NOT NULL,
  cluster VARCHAR(16) NOT NULL,
  service VARCHAR(12) NOT NULL,
  FOREIGN KEY (cluster) REFERENCES clusters(id),
  CHECK (service IN ('detector', 'scheduler')),
  CONSTRAINT name_cluster UNIQUE (name, cluster)
);

-- state: 'a' = active, 'd' = deleted
CREATE TABLE apikeys (
  access VARCHAR(16) UNIQUE NOT NULL,
  secret CHAR(64) NOT NULL,
  component VARCHAR(32) NOT NULL,
  lastused INTEGER,
  state CHAR(1) DEFAULT 'a',
  FOREIGN KEY (component) REFERENCES components(id)
);

CREATE TABLE notifications (
  id INTEGER PRIMARY KEY,
  context INTEGER NOT NULL,
  recipient CHAR(7),
  sender CHAR(7),
  timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  message TEXT NOT NULL
);

CREATE TABLE notifiers (
  name VARCHAR(32) PRIMARY KEY,
  type VARCHAR(16) NOT NULL,
  config TEXT
);

/* The language column allows an empty string as default because it is
 * acceptable to have some templates which are not language-specific, such as
 * a separator for use between versions in an e-mail.  Simply leaving as NULL
 * is unworkable because Postgres does not allow for NULL values in
 * multi-column keys.
 *
 * Ideally, the schema would prohibit creation of a template with both
 * variants where a language was defined and where one was not, as a template
 * should represent all languages or be language-agnostic.
 */
CREATE TABLE templates (
  name VARCHAR(32),
  language CHAR(2) NOT NULL DEFAULT '',
  content TEXT,
  PRIMARY KEY (name, language),
  CHECK (language IN ('', 'en', 'fr'))
);

CREATE TABLE reportables (
  id INTEGER PRIMARY KEY,
  epoch INTEGER NOT NULL,
  ticks INTEGER NOT NULL DEFAULT 1,
  cluster VARCHAR(16) NOT NULL,
  claimant CHAR(7),
  ticket_id INTEGER,
  ticket_no VARCHAR(9),
  summary TEXT,
  FOREIGN KEY (cluster) REFERENCES clusters(id)
);

/*
 * state: 'p' = pending/unactioned, 'a' = accepted, 'r' = rejected
 * resource: 'c' = CPU, 'g' = GPU
 * see burst.py::State, burst.py::Resource
 * submitters is an space-separated list of user IDs
 */
CREATE TABLE bursts (
  id INTEGER PRIMARY KEY,
  state CHAR(1) NOT NULL DEFAULT 'p',
  account VARCHAR(32) NOT NULL,
  resource CHAR(1) NOT NULL DEFAULT 'c',
  pain REAL NOT NULL,
  firstjob INTEGER NOT NULL,
  lastjob INTEGER NOT NULL,
  submitters TEXT NOT NULL,
  CHECK (state in ('p', 'a', 'r')),
  CHECK (resource in ('c', 'g')),
  FOREIGN KEY (id) REFERENCES reportables(id)
) WITHOUT ROWID;

-- tables keying to reportables must be declared as WITHOUT ROWID
-- so that the primary key is not tied to the row ID
CREATE TABLE job_ages (
  id INTEGER PRIMARY KEY,
  account VARCHAR(32) NOT NULL,
  submitter VARCHAR(32) NOT NULL,
  resource CHAR(1) NOT NULL DEFAULT 'c',
  age INTEGER NOT NULL,
  FOREIGN KEY (id) REFERENCES reportables(id)
) WITHOUT ROWID;

CREATE TABLE history (
  id INTEGER PRIMARY KEY,
  case_id INTEGER NOT NULL,
  analyst CHAR(7),
  timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  note TEXT,
  datum TEXT,
  was TEXT,
  now TEXT,
  FOREIGN KEY (case_id) REFERENCES reportables(id)
);
