-- cluster data
INSERT INTO clusters (id, name) VALUES ('testcluster', 'Test Cluster');

-- component data
INSERT INTO components (id, name, cluster, service) VALUES ('testcluster_detector', 'Detector', 'testcluster', 'detector');
INSERT INTO components (id, name, cluster, service) VALUES ('testcluster_scheduler', 'Adjustor', 'testcluster', 'scheduler');

-- API keys
INSERT INTO apikeys (access, secret, component) VALUES ('testapikey_d', 'WuHheVDysQQwdb+NK98w8EOHdiNUjLlz2Uxg/kIHqIGOek4DAmC5NCd2gZv7RQ==', 'testcluster_detector');
INSERT INTO apikeys (access, secret, component) VALUES ('testapikey_s', 'T3h5mwEk7mrVwxdon+s9blWhVh8zHDd7PVoUoWJsTf5Qd2EUie6I4pdBuyRykw==', 'testcluster_scheduler');

-- bursts
INSERT INTO reportables (epoch, cluster, summary) VALUES (1634316499, 'testcluster', '');
INSERT INTO bursts (id, account, pain, firstjob, lastjob, submitters) VALUES (1, 'def-pi1', 1.00, 1005, 2000, 'user3');

INSERT INTO templates (name, language, content) VALUES (
  'impossible title', 'en', 'NOTICE: Your computations on {cluster} may be optimized');
INSERT INTO templates (name, language, content) VALUES (
  'impossible', 'en', 'Hello {piName},

Our records show that your account ''{account}'' has a quantity of resources waiting in the job queue on {cluster} which could experience substantial wait time. Upon inspection of your recent job history it has come to our attention that there may be job submission parameter changes which could alleviate the occurrence of these anticipated wait times.

If you would like to discuss this potential job submission parameter changes you can respond to this message and we will follow up with more details.

Best regards,

{analyst}
Compute Canada Support


Additional job info:
  Current jobs: {num_jobs}
  Submitters:   {submitters}
');

INSERT INTO templates (name, language, content) VALUES (
  'impossible title', 'fr', 'AVIS: Vos calculs sur {cluster} peuvent être optimisés');
INSERT INTO templates (name, language, content) VALUES (
  'impossible', 'fr', 'Bonjour {piName},

Nos enregistrements montrent que votre compte ''{account}'' a une quantité de ressources en attente dans la file d''attente des travaux sur {cluster} qui pourrait connaître un temps d''attente substantiel. Après examen de votre historique d''emploi récent, nous avons appris qu''il pourrait y avoir des changements dans les paramètres de soumission des emplois qui pourraient réduire l''occurrence de ces temps d''attente prévus.

Si vous souhaitez discuter de ces modifications potentielles des paramètres de soumission de travail, vous pouvez répondre à ce message et nous vous donnerons plus de détails. 

Meilleures salutations,

{analyst}
Compute Canada Support


Info additionel au tâches:
  Tâches au courant:   {num_jobs}
  Emetteurs de tâches: {submitters}
');

INSERT INTO templates (name, language, content) VALUES (
  'rac title', 'en', 'NOTICE: Your computations on {cluster} may indicate a need for an ongoing allocation');
INSERT INTO templates (name, language, content) VALUES (
  'rac', 'en', 'Hello {piName},

Our records show that your account ''{accounts}'' has a quantity of resources waiting in the job queue on {cluster} which could experience substantial
 wait time. Upon inspection of your recent job history it has come to our attention that your account''s recent usage is already above the expected u
sage rate of the account type. If it is anticipated that the account should be able to sustain greater that it is currently experiencing we recommend
 that the workload be distributed across multiple Compute Canada systems or that you apply for increased resource access via the Resource Allocation
Competition (RAC) in future call of the program.

If you would like to discuss these potential options for increasing the sustained throughput of your projects at Compute Canada you can respond to th
is message and we will follow up with more details.

Best regards,

{analyst}
Compute Canada Support


Additional job info:
  Current jobs: {num_jobs}
  Submitters:   {submitters}
');

INSERT INTO templates (name, language, content) VALUES (
  'rac title', 'fr', 'AVIS: Vos calculs sur {cluster} peuvent indiquer la nécessité d''une allocation continue');
INSERT INTO templates (name, language, content) VALUES (
  'rac', 'fr', 'Bonjour {piName},

Nos archives montrent que votre compte ''{accounts}'' a une quantité de ressources en attente dans la file d''attente des tâches sur {cluster} qui po
urrait connaître un temps d''attente substantiel. Après examen de l''historique de vos travaux récents, nous avons constaté que l''utilisation récent
e de votre compte est déjà supérieure au taux d''utilisation prévu du type de compte. Si l''on prévoit que le compte devrait être en mesure de se mai
ntenir plus longtemps que ce qu''il connaît actuellement, nous vous recommandons de répartir la charge de travail sur plusieurs systèmes de Calcul Ca
nada ou de demander un accès accru aux ressources via le concours d''allocation de ressources (RAC) lors d''un prochain appel de le programme.

Si vous souhaitez discuter de ces options potentielles pour augmenter le débit soutenu de vos projets chez Compute Canada, vous pouvez répondre à ce
message et nous vous donnerons plus de détails.

Meilleures salutations,

{analyst}
Compute Canada Support


Info additionel au tâches:
  Tâches au courant:   {num_jobs}
  Emetteurs de tâches: {submitters}
');

INSERT INTO templates (name, language, content) VALUES (
  'candidate title', 'en', 'NOTICE: Your computations on {cluster} may be eligible for prioritised execution');
INSERT INTO templates (name, language, content) VALUES (
  'candidate', 'en', 'Hello {piName},

Our records show that your account ''{accounts}'' has a quantity of resources waiting in the job queue on {cluster} which could experience substantial
 wait time. Considering this pending work load along with the account''s recent usage history we may be able to provide a transient increase of prior
ity to decrease these anticipated wait times.

If you would like to discuss this potential transient priority change to {account} you can respond to this message and we will follow up with more de
tails.

Best regards,

{analyst}
Compute Canada Support


Additional job info:
  Current jobs: {num_jobs}
  Submitters:   {submitters}
');

INSERT INTO templates (name, language, content) VALUES (
  'candidate title', 'fr', 'AVIS: Vos calculs sur {cluster} peuvent être éligibles pour une exécution prioritaire');
INSERT INTO templates (name, language, content) VALUES (
  'candidate', 'fr', 'Bonjour {piName},

Nos archives montrent que votre compte ''{accounts}'' a une quantité de ressources en attente dans la file d''attente des tâches sur {cluster} qui po
urrait connaître un temps d''attente substantiel. Compte tenu de cette charge de travail en attente ainsi que de l''historique d''utilisation récent
du compte, nous pourrions être en mesure de fournir une augmentation transitoire de la priorité pour réduire ces temps d''attente prévus.

Si vous souhaitez discuter de ce changement de priorité transitoire potentiel vers {account} vous pouvez répondre à ce message et nous vous donneron
s plus de détails.

Meilleures salutations,

{analyst}
Compute Canada Support


Info additionel au tâches:
  Tâches au courant:   {num_jobs}
  Emetteurs de tâches: {submitters}
');
INSERT INTO notifiers (name, type, config) VALUES ('Test Notifier', 'test', '{}');
