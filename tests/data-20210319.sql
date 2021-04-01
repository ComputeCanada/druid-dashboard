#INSERT INTO clusters (id, name) VALUES ('testcluster', 'Test Cluster');
#INSERT INTO clusters (id, name) VALUES ('testcluster2', 'Test Cluster 2');
#INSERT INTO components (id, name, cluster, service) VALUES ('testcluster_detector', 'Detector', 'testcluster', 'detector');
INSERT INTO components (id, name, cluster, service) VALUES ('testcluster_scheduler', 'Scheduler', 'testcluster', 'scheduler');
INSERT INTO components (id, name, cluster, service) VALUES ('testcluster2_detector', 'Detector', 'testcluster2', 'detector');
INSERT INTO components (id, name, cluster, service) VALUES ('testcluster2_scheduler', 'Scheduler', 'testcluster2', 'scheduler');

UPDATE apikeys SET access = 'testapikey_d', lastused = 20 WHERE access = 'testapikey';
INSERT INTO apikeys (access, secret, component, lastused) VALUES (
  'testapikey_s', 'T3h5mwEk7mrVwxdon+s9blWhVh8zHDd7PVoUoWJsTf5Qd2EUie6I4pdBuyRykw==', 'testcluster_scheduler', 20);
INSERT INTO apikeys (access, secret, component, lastused) VALUES (
  'fakeyfakefake', 'ZoHCik4dOZm4VvKnkQUv9lcWydR8aH4bNCW2/fwxGGOfbj5SrBAY50nD3gNCIA==', 'testcluster_detector', 10);

INSERT INTO apikeys (access, secret, component, lastused) VALUES (
  'testapikey2_d', 'rammarammadingdong', 'testcluster2_detector', 20);
INSERT INTO apikeys (access, secret, component, lastused) VALUES (
  'testapikey2_s', 'GEMr1Ksi7I9G9BXuAhY4IITgMcyAKmHzgjFZ2uBTUpQkT1n3xUda5v+4FQAaBA==', 'testcluster2_scheduler', 20);
INSERT INTO bursts (account, cluster, pain, firstjob, lastjob, state, epoch) VALUES ('def-bbb-aa', 'testcluster', 2.0, 11, 21, 'a', 20);
INSERT INTO bursts (account, cluster, pain, firstjob, lastjob, state, epoch) VALUES ('def-ccc-aa', 'testcluster', 2.0, 12, 22, 'a', 20);
UPDATE bursts SET state = 'a' WHERE cluster = 'testcluster' AND account IN ('def-bbb-aa', 'def-ccc-aa');
