DROP TABLE IF EXISTS schemalog;
DROP TABLE IF EXISTS apikeys;
DROP TABLE IF EXISTS notifications;

CREATE TABLE schemalog (
  version INTEGER PRIMARY KEY,
  applied TIMESTAMP
);
INSERT INTO schemalog (version, applied) VALUES ('20201209', CURRENT_TIMESTAMP);

CREATE TABLE apikeys (
  access VARCHAR(16) UNIQUE NOT NULL,
  secret CHAR(64) NOT NULL
);

CREATE TABLE notifications (
  id INTEGER PRIMARY KEY,
  context INTEGER NOT NULL,
  recipient CHAR(7),
  sender CHAR(7),
  timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  message TEXT NOT NULL
);
