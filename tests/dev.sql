INSERT INTO clusters (id, name) 
  VALUES ('testcluster', 'Test Cluster');
INSERT INTO components (id, name, cluster, service)
  VALUES ('testcluster_detector', 'Detector', 'testcluster', 'detector');
INSERT INTO components (id, name, cluster, service)
  VALUES ('testcluster_scheduler', 'Scheduler', 'testcluster', 'scheduler');
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
