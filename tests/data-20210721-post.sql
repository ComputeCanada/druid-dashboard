UPDATE templates SET pi_only = FALSE where name='impossible';
UPDATE templates_content SET label = 'Impossible jobs' WHERE template = 'impossible' AND language = 'en';
UPDATE templates SET pi_only = TRUE where name='candidate';
UPDATE templates_content SET label = 'Potential burst candidate' WHERE template = 'candidate' AND language = 'en';
UPDATE templates SET pi_only = TRUE where name='rac';
UPDATE templates_content SET label = 'Potential RAC candidate' WHERE template = 'rac' AND language = 'en';
INSERT INTO appropriate_templates VALUES ('bursts', 'impossible', CAST (1 AS BOOLEAN));
INSERT INTO appropriate_templates VALUES ('bursts', 'rac', CAST (1 AS BOOLEAN));
INSERT INTO appropriate_templates VALUES ('bursts', 'candidate', CAST (1 AS BOOLEAN));
