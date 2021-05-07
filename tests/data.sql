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
INSERT INTO bursts (account, cluster, pain, firstjob, lastjob, submitters, epoch, summary) VALUES ('def-pi1', 'testcluster', 1.0, 10, 20, 'userQ', 10, '{"num_jobs":1403}');
INSERT INTO bursts (account, cluster, pain, firstjob, lastjob, submitters, epoch, summary) VALUES ('def-aaa-aa', 'testcluster', 1.0, 10, 20, 'userQ', 10, '{"num_jobs":1403}');
INSERT INTO bursts (account, cluster, pain, firstjob, lastjob, submitters, epoch) VALUES ('def-bbb-aa', 'testcluster', 1.0, 11, 21, 'userQ', 10);
INSERT INTO bursts (account, cluster, pain, firstjob, lastjob, submitters, epoch) VALUES ('def-aaa-aa', 'testcluster', 2.0, 10, 20, 'userQ', 20);
INSERT INTO bursts (account, cluster, pain, firstjob, lastjob, submitters, state, epoch) VALUES ('def-bbb-aa', 'testcluster', 2.0, 11, 21, 'userQ', 'a', 20);
INSERT INTO bursts (account, cluster, pain, firstjob, lastjob, submitters, state, epoch) VALUES ('def-ccc-aa', 'testcluster', 2.0, 12, 22, 'userQ', 'a', 20);
INSERT INTO bursts (account, cluster, pain, firstjob, lastjob, submitters, epoch) VALUES ('def-aaa-aa', 'testcluster2', 1.5, 15, 25, 'userQ', 15);
INSERT INTO bursts (account, cluster, pain, firstjob, lastjob, submitters, epoch) VALUES ('def-bbb-aa', 'testcluster2', 1.5, 16, 26, 'userQ', 15);
INSERT INTO bursts (account, cluster, pain, firstjob, lastjob, submitters, epoch) VALUES ('def-aaa-aa', 'testcluster2', 2.5, 15, 25, 'userQ', 25);
INSERT INTO bursts (account, cluster, pain, firstjob, lastjob, submitters, epoch) VALUES ('def-bbb-aa', 'testcluster2', 2.5, 16, 26, 'userQ', 25);
INSERT INTO bursts (account, cluster, pain, firstjob, lastjob, submitters, epoch) VALUES ('def-ccc-aa', 'testcluster2', 2.5, 17, 27, 'userQ', 25);

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
  'intro title', 'en', 'NOTICE: Your computations on %cluster% may be eligible for prioritised execution');
INSERT INTO templates (name, language, content) VALUES (
  'intro title', 'fr', 'AVIS: Vos calculs à %cluster% peuvent être éligibles pour une exécution prioritaire');
INSERT INTO templates (name, language, content) VALUES (
  'intro', 'en', 'Hello %piName%,

Ongoing analysis of queued jobs on %cluster% has shown that your project has a quantity of jobs that would benefit from a temporary escalation in priority.  Please let us know by replying to this message if you are interested.

Additional job info:
  Current jobs: %num_jobs%
  Submitters:   %submitters%

Best regards,
%analyst%');
INSERT INTO templates (name, language, content) VALUES (
  'intro', 'fr', 'Bonjour %piName%,

Analyse en cours des travaux en attente sur %cluster% a montré que votre projet comporte une quantité de tâches bénéficier d''une escalade temporaire en priorité. S''il vous plaît laissez-nous savoir par répondre à ce message si vous êtes intéressé.

Info additionel au tâches:
  Tâches au courant:   %num_jobs%
  Emetteurs de tâches: %submitters%

Meilleures salutations,
%analyst%');

/* ---------------------------------------------------------------------------
                                                          pilot templates
These are what we'll use actively.  Putting them here for convenience and
also in case we use them for testing at some point.
--------------------------------------------------------------------------- */

INSERT INTO templates (name, language, content) VALUES (
  'candidate title', 'en', 'NOTICE: Your computations on %cluster% may be eligible for prioritised execution');
INSERT INTO templates (name, language, content) VALUES (
  'candidate', 'en', 'Hello %piName%,

Our records show that your account ''%account%'' has a quantity of resources waiting in the job queue on %cluster% which could experience substantial wait time. Considering this pending work load along with the account''s recent usage history we may be able to provide a transient increase of priority to decrease these anticipated wait times.

If you would like to discuss this potential transient priority change to %account% you can respond to this message and we will follow up with more details.

Best regards,

%analyst%
Compute Canada Support


Additional job info:
  Current jobs: %num_jobs%
  Submitters:   %submitters%
');

INSERT INTO templates (name, language, content) VALUES (
  'candidate title', 'fr', 'AVIS: Vos calculs sur %cluster% peuvent être éligibles pour une exécution prioritaire');
INSERT INTO templates (name, language, content) VALUES (
  'candidate', 'fr', 'Bonjour %piName%,

Nos archives montrent que votre compte ''% account%'' a une quantité de ressources en attente dans la file d''attente des tâches sur %cluster% qui pourrait connaître un temps d''attente substantiel. Compte tenu de cette charge de travail en attente ainsi que de l''historique d''utilisation récent du compte, nous pourrions être en mesure de fournir une augmentation transitoire de la priorité pour réduire ces temps d''attente prévus.

Si vous souhaitez discuter de ce changement de priorité transitoire potentiel vers% account%, vous pouvez répondre à ce message et nous vous donnerons plus de détails.

Meilleures salutations,

%analyst%
Compute Canada Support


Info additionel au tâches:
  Tâches au courant:   %num_jobs%
  Emetteurs de tâches: %submitters%
');

INSERT INTO templates (name, language, content) VALUES (
  'impossible title', 'en', 'NOTICE: Your computations on %cluster% may be optimized');
INSERT INTO templates (name, language, content) VALUES (
  'impossible', 'en', 'Hello %piName%,

Our records show that your account ''%account%'' has a quantity of resources waiting in the job queue on %cluster% which could experience substantial wait time. Upon inspection of your recent job history it has come to our attention that there may be job submission parameter changes which could alleviate the occurrence of these anticipated wait times.

If you would like to discuss this potential job submission parameter changes you can respond to this message and we will follow up with more details.

Best regards,

%analyst%
Compute Canada Support


Additional job info:
  Current jobs: %num_jobs%
  Submitters:   %submitters%
');

INSERT INTO templates (name, language, content) VALUES (
  'impossible title', 'fr', 'AVIS: Vos calculs sur %cluster% peuvent être optimisés');
INSERT INTO templates (name, language, content) VALUES (
  'impossible', 'fr', 'Bonjour %piName%,

Nos enregistrements montrent que votre compte ''% account%'' a une quantité de ressources en attente dans la file d''attente des travaux sur %cluster% qui pourrait connaître un temps d''attente substantiel. Après examen de votre historique d''emploi récent, nous avons appris qu''il pourrait y avoir des changements dans les paramètres de soumission des emplois qui pourraient réduire l''occurrence de ces temps d''attente prévus.

Si vous souhaitez discuter de ces modifications potentielles des paramètres de soumission de travail, vous pouvez répondre à ce message et nous vous donnerons plus de détails. 

Meilleures salutations,

%analyst%
Compute Canada Support


Info additionel au tâches:
  Tâches au courant:   %num_jobs%
  Emetteurs de tâches: %submitters%
');

INSERT INTO templates (name, language, content) VALUES (
  'rac title', 'en', 'NOTICE: Your computations on %cluster% may indicate a need for an ongoing allocation');
INSERT INTO templates (name, language, content) VALUES (
  'rac', 'en', 'Hello %piName%,

Our records show that your account ''%account%'' has a quantity of resources waiting in the job queue on %cluster% which could experience substantial wait time. Upon inspection of your recent job history it has come to our attention that your account''s recent usage is already above the expected usage rate of the account type. If it is anticipated that the account should be able to sustain greater that it is currently experiencing we recommend that the workload be distributed across multiple Compute Canada systems or that you apply for increased resource access via the Resource Allocation Competition (RAC) in future call of the program.

If you would like to discuss these potential options for increasing the sustained throughput of your projects at Compute Canada you can respond to this message and we will follow up with more details.

Best regards,

%analyst%
Compute Canada Support


Additional job info:
  Current jobs: %num_jobs%
  Submitters:   %submitters%
');

INSERT INTO templates (name, language, content) VALUES (
  'rac title', 'fr', 'AVIS: Vos calculs sur %cluster% peuvent indiquer la nécessité d''une allocation continue');
INSERT INTO templates (name, language, content) VALUES (
  'rac', 'fr', 'Bonjour %piName%,

Nos archives montrent que votre compte ''% account%'' a une quantité de ressources en attente dans la file d''attente des tâches sur %cluster% qui pourrait connaître un temps d''attente substantiel. Après examen de l''historique de vos travaux récents, nous avons constaté que l''utilisation récente de votre compte est déjà supérieure au taux d''utilisation prévu du type de compte. Si l''on prévoit que le compte devrait être en mesure de se maintenir plus longtemps que ce qu''il connaît actuellement, nous vous recommandons de répartir la charge de travail sur plusieurs systèmes de Calcul Canada ou de demander un accès accru aux ressources via le concours d''allocation de ressources (RAC) lors d''un prochain appel de le programme.

Si vous souhaitez discuter de ces options potentielles pour augmenter le débit soutenu de vos projets chez Compute Canada, vous pouvez répondre à ce message et nous vous donnerons plus de détails.

Meilleures salutations, 

%analyst%
Compute Canada Support


Info additionel au tâches:
  Tâches au courant:   %num_jobs%
  Emetteurs de tâches: %submitters%
');

INSERT INTO notifiers (name, type, config) VALUES ('Test Notifier', 'test', '{}');
