DROP TABLE IF EXISTS schemalog;
DROP TABLE IF EXISTS apikeys;
DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS components;
DROP TABLE IF EXISTS bursts;
DROP TABLE IF EXISTS clusters;

CREATE TABLE schemalog (
  version VARCHAR(10) PRIMARY KEY,
  applied TIMESTAMP
);
INSERT INTO schemalog (version, applied) VALUES ('20210203', CURRENT_TIMESTAMP);

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

-- state: 'a' = accepted, 'p' = pending, 'r' = rejected
CREATE TABLE bursts (
  id INTEGER PRIMARY KEY,
  state CHAR(1) NOT NULL DEFAULT 'p',
  account VARCHAR(32) NOT NULL,
  cluster VARCHAR(16) NOT NULL,
  pain REAL NOT NULL,
  firstjob INTEGER NOT NULL,
  lastjob INTEGER NOT NULL,
  summary TEXT,
  epoch INTEGER NOT NULL,
  FOREIGN KEY (cluster) REFERENCES clusters(id)
);