INSERT INTO clusters (id, name) VALUES ('testcluster', 'Test Cluster');
INSERT INTO clusters (id, name) VALUES ('testcluster2', 'Test Cluster 2');
INSERT INTO components (id, name, cluster, service) VALUES ('testcluster_detector', 'Detector', 'testcluster', 'detector');
INSERT INTO components (id, name, cluster, service) VALUES ('testcluster_scheduler', 'Scheduler', 'testcluster', 'scheduler');
INSERT INTO components (id, name, cluster, service) VALUES ('testcluster2_detector', 'Detector', 'testcluster2', 'detector');
INSERT INTO components (id, name, cluster, service) VALUES ('testcluster2_scheduler', 'Scheduler', 'testcluster2', 'scheduler');
-- test api keys
-- secret is generated with
-- `dd if=/dev/urandom bs=1 count=46 2>/dev/null | base64`
INSERT INTO apikeys (access, secret, component, lastused) VALUES (
  'testapikey_d', 'WuHheVDysQQwdb+NK98w8EOHdiNUjLlz2Uxg/kIHqIGOek4DAmC5NCd2gZv7RQ==', 'testcluster_detector', 20);
INSERT INTO apikeys (access, secret, component, lastused) VALUES (
  'testapikey_s', 'T3h5mwEk7mrVwxdon+s9blWhVh8zHDd7PVoUoWJsTf5Qd2EUie6I4pdBuyRykw==', 'testcluster_scheduler', 20);
INSERT INTO apikeys (access, secret, component, lastused) VALUES (
  'fakeyfakefake', 'ZoHCik4dOZm4VvKnkQUv9lcWydR8aH4bNCW2/fwxGGOfbj5SrBAY50nD3gNCIA==', 'testcluster_detector', 10);
-- testcluster2 components are ONLY used for testing a specific case (test_get_components_lastheard)
-- and if used for anything else will break this test (because use of the key causes an update to
-- the last-heard-from property of the component.  Without this we have to force a one-second sleep
-- in the tests, which is obnoxious.
INSERT INTO apikeys (access, secret, component, lastused) VALUES (
  'testapikey2_d', 'rammarammadingdong', 'testcluster2_detector', 20);
INSERT INTO apikeys (access, secret, component, lastused) VALUES (
  'testapikey2_s', 'GEMr1Ksi7I9G9BXuAhY4IITgMcyAKmHzgjFZ2uBTUpQkT1n3xUda5v+4FQAaBA==', 'testcluster2_scheduler', 20);
INSERT INTO bursts (account, cluster, pain, firstjob, lastjob, epoch) VALUES ('def-aaa-aa', 'testcluster', 1.0, 10, 20, 10);
INSERT INTO bursts (account, cluster, pain, firstjob, lastjob, epoch) VALUES ('def-bbb-aa', 'testcluster', 1.0, 11, 21, 10);
INSERT INTO bursts (account, cluster, pain, firstjob, lastjob, epoch) VALUES ('def-aaa-aa', 'testcluster', 2.0, 10, 20, 20);
INSERT INTO bursts (account, cluster, pain, firstjob, lastjob, state, epoch) VALUES ('def-bbb-aa', 'testcluster', 2.0, 11, 21, 'a', 20);
INSERT INTO bursts (account, cluster, pain, firstjob, lastjob, state, epoch) VALUES ('def-ccc-aa', 'testcluster', 2.0, 12, 22, 'a', 20);
INSERT INTO bursts (account, cluster, pain, firstjob, lastjob, epoch) VALUES ('def-aaa-aa', 'testcluster2', 1.5, 15, 25, 15);
INSERT INTO bursts (account, cluster, pain, firstjob, lastjob, epoch) VALUES ('def-bbb-aa', 'testcluster2', 1.5, 16, 26, 15);
INSERT INTO bursts (account, cluster, pain, firstjob, lastjob, epoch) VALUES ('def-aaa-aa', 'testcluster2', 2.5, 15, 25, 25);
INSERT INTO bursts (account, cluster, pain, firstjob, lastjob, epoch) VALUES ('def-bbb-aa', 'testcluster2', 2.5, 16, 26, 25);
INSERT INTO bursts (account, cluster, pain, firstjob, lastjob, epoch) VALUES ('def-ccc-aa', 'testcluster2', 2.5, 17, 27, 25);
