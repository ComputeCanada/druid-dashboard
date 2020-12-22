-- test api keys
-- secret is generated with
-- `dd if=/dev/urandom bs=1 count=46 2>/dev/null | base64`
INSERT INTO apikeys (access, secret) VALUES (
  'testapikey', 'WuHheVDysQQwdb+NK98w8EOHdiNUjLlz2Uxg/kIHqIGOek4DAmC5NCd2gZv7RQ==');
