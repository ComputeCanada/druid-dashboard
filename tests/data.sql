INSERT INTO clusters (id, name) VALUES ('testcluster', 'Test Cluster');
INSERT INTO clusters (id, name) VALUES ('testcluster2', 'Test Cluster 2');
INSERT INTO components (id, name, cluster, service) VALUES ('testcluster_detector', 'Detector', 'testcluster', 'detector');
-- test api keys
-- secret is generated with
-- `dd if=/dev/urandom bs=1 count=46 2>/dev/null | base64`
INSERT INTO apikeys (access, secret, component) VALUES (
  'testapikey', 'WuHheVDysQQwdb+NK98w8EOHdiNUjLlz2Uxg/kIHqIGOek4DAmC5NCd2gZv7RQ==', 'testcluster_detector');
INSERT INTO apikeys (access, secret, component) VALUES (
  'fakeyfakefake', 'ZoHCik4dOZm4VvKnkQUv9lcWydR8aH4bNCW2/fwxGGOfbj5SrBAY50nD3gNCIA==', 'testcluster_detector');
INSERT INTO bursts (account, cluster, pain, firstjob, lastjob, epoch) VALUES ('def-aaa-aa', 'testcluster', 1.0, 10, 20, 10);
INSERT INTO bursts (account, cluster, pain, firstjob, lastjob, epoch) VALUES ('def-bbb-aa', 'testcluster', 1.0, 11, 21, 10);
INSERT INTO bursts (account, cluster, pain, firstjob, lastjob, epoch) VALUES ('def-aaa-aa', 'testcluster', 2.0, 10, 20, 20);
INSERT INTO bursts (account, cluster, pain, firstjob, lastjob, epoch) VALUES ('def-bbb-aa', 'testcluster', 2.0, 11, 21, 20);
INSERT INTO bursts (account, cluster, pain, firstjob, lastjob, epoch) VALUES ('def-ccc-aa', 'testcluster', 2.0, 12, 22, 20);
INSERT INTO bursts (account, cluster, pain, firstjob, lastjob, epoch) VALUES ('def-aaa-aa', 'testcluster2', 1.5, 15, 25, 15);
INSERT INTO bursts (account, cluster, pain, firstjob, lastjob, epoch) VALUES ('def-bbb-aa', 'testcluster2', 1.5, 16, 26, 15);
INSERT INTO bursts (account, cluster, pain, firstjob, lastjob, epoch) VALUES ('def-aaa-aa', 'testcluster2', 2.5, 15, 25, 25);
INSERT INTO bursts (account, cluster, pain, firstjob, lastjob, epoch) VALUES ('def-bbb-aa', 'testcluster2', 2.5, 16, 26, 25);
INSERT INTO bursts (account, cluster, pain, firstjob, lastjob, epoch) VALUES ('def-ccc-aa', 'testcluster2', 2.5, 17, 27, 25);
