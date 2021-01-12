INSERT INTO clusters (id, name) 
  VALUES ('testcluster', 'Test Cluster');
INSERT INTO clusters (id, name)
  VALUES ('protocluster', 'Prototype Cluster');
INSERT INTO components (id, name, cluster, service)
  VALUES ('testcluster_detector', 'Detector', 'testcluster', 'detector');
INSERT INTO components (id, name, cluster, service)
  VALUES ('testcluster_scheduler', 'Scheduler', 'testcluster', 'scheduler');
INSERT INTO components (id, name, cluster, service)
  VALUES ('protocluster_detector', 'Detector', 'protocluster', 'detector');
INSERT INTO components (id, name, cluster, service)
  VALUES ('protocluster_scheduler', 'Scheduler', 'protocluster', 'scheduler');
-- test api keys
-- secret is generated with
-- `dd if=/dev/urandom bs=1 count=48 2>/dev/null | base64`
INSERT INTO apikeys (access, secret, component) VALUES (
  'testapikey',
  'WuHheVDysQQwdb+NK98w8EOHdiNUjLlz2Uxg/kIHqIGOek4DAmC5NCd2gZv7RQ==',
  'testcluster_detector');
INSERT INTO apikeys (access, secret, component) VALUES (
  'testapikey2',
  't7zP2drVPhV9MdTypAsggshp2PQnpLS7ENVJq+P+BhAVJRMjmhInj6D7IP0tOcEz',
  'testcluster_scheduler');
INSERT INTO apikeys (access, secret, component) VALUES (
  'protoapikey1',
  '4XLKOa2g2+YhwKnZvr5tNb4Es18Fdh546ifxi3UyH8eyK7rqVSUFUuH7yhHqpEgV',
  'protocluster_detector');
INSERT INTO apikeys (access, secret, component) VALUES (
  'protoapikey2',
  'OZnsHx/jW0Ymp/urRag4rP8zd+PEnlczqVZIl5hLDcvQc9r19i0ZO15UyPeid158',
  'protocluster_scheduler');
