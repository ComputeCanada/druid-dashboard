UPDATE bursts SET submitters = 'userQ';
UPDATE bursts SET summary = '{"num_jobs":1403}' WHERE account = 'def-aaa-aa' AND cluster = 'testcluster';

-- template data
INSERT INTO templates (name, language, content) VALUES (
  'other language follows', 'fr', '
(La version française de ce message suit.)
');
INSERT INTO templates (name, language, content) VALUES (
  'other language follows', 'en', '
(The English language version of this message follows.)
');
INSERT INTO templates (name, content) VALUES (
  'separator', '
--------------------------------------
');
INSERT INTO templates (name, language, content) VALUES (
  'intro title', 'en', 'NOTICE: Your computations may be eligible for prioritised execution');
INSERT INTO templates (name, language, content) VALUES (
  'intro title', 'fr', 'AVIS: Vos calculs peuvent être éligibles pour une exécution prioritaire');
INSERT INTO templates (name, language, content) VALUES (
  'intro', 'en', 'Hello %piName%,

Ongoing analysis of queued jobs on %cluster% has shown that your project has a quantity of jobs that would benefit from a temporary escalation in priority.  Please let us know by replying to this message if you are interested.

Additional job info:
  Current number of jobs: %num_jobs%

Best regards,
%analyst%');
INSERT INTO templates (name, language, content) VALUES (
  'intro', 'fr', 'Bonjour %piName%,

Analyse en cours des travaux en attente sur %cluster% a montré que votre projet comporte une quantité de tâches bénéficier d''une escalade temporaire en priorité. S''il vous plaît laissez-nous savoir par répondre à ce message si vous êtes intéressé.

Info additionel au tâches:
  Comte de tâches au courant: %num_jobs%

Meilleures salutations,
%analyst%');
