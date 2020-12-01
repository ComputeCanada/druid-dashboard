-- test api keys
-- secret is generated with
-- `dd if=/dev/urandom bs=1 count=46 2>/dev/null | base64`
INSERT INTO apikeys (access, secret) VALUES (
  'testapikey', 'WuHheVDysQQwdb+NK98w8EOHdiNUjLlz2Uxg/kIHqIGOek4DAmC5NCd2gZv7RQ==');
INSERT INTO apikeys (access, secret) VALUES (
  'fakeyfakefake', 'ZoHCik4dOZm4VvKnkQUv9lcWydR8aH4bNCW2/fwxGGOfbj5SrBAY50nD3gNCIA==');
