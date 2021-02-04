DROP TABLE IF EXISTS schemalogTMP;
CREATE TABLE schemalogTMP (
  version VARCHAR(10) PRIMARY KEY,
  applied TIMESTAMP
);
INSERT INTO schemalogTMP SELECT * FROM schemalog;
DROP TABLE schemalog;
ALTER TABLE schemalogTMP RENAME TO schemalog;

INSERT INTO schemalog (version, applied) VALUES ('20210203', CURRENT_TIMESTAMP);
