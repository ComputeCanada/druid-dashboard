DROP TABLE IF EXISTS schemalog;
DROP TABLE IF EXISTS apikeys;
DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS components;
DROP TABLE IF EXISTS clusters;

CREATE TABLE schemalog (
  version INTEGER PRIMARY KEY,
  applied TIMESTAMP
);
INSERT INTO schemalog (version, applied) VALUES ('20201209', CURRENT_TIMESTAMP);

CREATE TABLE clusters (
  id VARCHAR(16) UNIQUE NOT NULL,
  name VARCHAR(32) UNIQUE NOT NULL
);

CREATE TABLE components (
  id VARCHAR(32) UNIQUE NOT NULL,
  name VARCHAR(64) UNIQUE NOT NULL,
  cluster VARCHAR(16) NOT NULL,
  service VARCHAR(12) NOT NULL,
  FOREIGN KEY (cluster) REFERENCES clusters(id),
  CHECK (service IN ('detector', 'scheduler'))
);

-- state: 'a' = active, 'd' = deleted
CREATE TABLE apikeys (
  access VARCHAR(16) UNIQUE NOT NULL,
  secret CHAR(64) NOT NULL,
  component VARCHAR(32) NOT NULL,
  lastused TIMESTAMP,
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
