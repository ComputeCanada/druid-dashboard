-- template data
INSERT INTO templates (name) VALUES ('other language follows');
INSERT INTO templates_content (template, label, language, body) VALUES (
  'other language follows', 'other language follows', 'fr', '
(La version française de ce message suit.)
');
INSERT INTO templates_content (template, label, language, body) VALUES (
  'other language follows', 'other language follows', 'en', '
(The English language version of this message follows.)
');

INSERT INTO templates (name) VALUES ('separator');
INSERT INTO templates_content (template, label, body) VALUES (
  'separator', 'separator', '
--------------------------------------
');

INSERT INTO templates (name) VALUES ('intro');
INSERT INTO templates_content (template, label, language, title, body) VALUES (
  'intro', 'intro', 'en',
  'NOTICE: Your computations on {cluster} may be eligible for prioritised execution',
  'Hello {piName},

Ongoing analysis of queued jobs on {cluster} has shown that your project has a quantity of jobs that would benefit from a temporary escalation in priority.  Please let us know by replying to this message if you are interested.

Additional job info:
  Current jobs: {num_jobs}
  Submitters:   {submitters}

Best regards,
{analyst}');
INSERT INTO templates_content (template, label, language, title, body) VALUES (
  'intro', 'intro', 'fr',
  'AVIS: Vos calculs à {cluster} peuvent être éligibles pour une exécution prioritaire', 
  'Bonjour {piName},

Analyse en cours des travaux en attente sur {cluster} a montré que votre projet comporte une quantité de tâches bénéficier d''une escalade temporaire en priorité. S''il vous plaît laissez-nous savoir par répondre à ce message si vous êtes intéressé.

Info additionel au tâches:
  Tâches au courant:   {num_jobs}
  Emetteurs de tâches: {submitters}

Meilleures salutations,
{analyst}');

/* ---------------------------------------------------------------------------
                                                          pilot templates
These are what we'll use actively.  Putting them here for convenience and
also in case we use them for testing at some point.
--------------------------------------------------------------------------- */

INSERT INTO templates (name) VALUES ('candidate');
INSERT INTO templates_content (template, label, language, title, body) VALUES (
  'candidate', 'candidate', 'en',
  'NOTICE: Your computations on {cluster} may be eligible for prioritised execution',
  'Hello {piName},

Our records show that your account ''{account}'' has a quantity of resources waiting in the job queue on {cluster} which could experience substantial wait time. Considering this pending work load along with the account''s recent usage history we may be able to provide a transient increase of priority to decrease these anticipated wait times.

If you would like to discuss this potential transient priority change to {account} you can respond to this message and we will follow up with more details.

Best regards,

{analyst}
Compute Canada Support


Additional job info:
  Current jobs: {num_jobs}
  Submitters:   {submitters}
');

INSERT INTO templates_content (template, label, language, title, body) VALUES (
  'candidate', 'candidate', 'fr',
  'AVIS: Vos calculs sur {cluster} peuvent être éligibles pour une exécution prioritaire',
  'Bonjour {piName},

Nos archives montrent que votre compte ''{account}'' a une quantité de ressources en attente dans la file d''attente des tâches sur {cluster} qui pourrait connaître un temps d''attente substantiel. Compte tenu de cette charge de travail en attente ainsi que de l''historique d''utilisation récent du compte, nous pourrions être en mesure de fournir une augmentation transitoire de la priorité pour réduire ces temps d''attente prévus.

Si vous souhaitez discuter de ce changement de priorité transitoire potentiel vers{ account}, vous pouvez répondre à ce message et nous vous donnerons plus de détails.

Meilleures salutations,

{analyst}
Compute Canada Support


Info additionel au tâches:
  Tâches au courant:   {num_jobs}
  Emetteurs de tâches: {submitters}
');

INSERT INTO templates (name) VALUES ('impossible');
INSERT INTO templates_content (template, label, language, title, body) VALUES (
  'impossible', 'impossible', 'en', 'NOTICE: Your computations on {cluster} may be optimized',
  'Hello {piName},

Our records show that your account ''{account}'' has a quantity of resources waiting in the job queue on {cluster} which could experience substantial wait time. Upon inspection of your recent job history it has come to our attention that there may be job submission parameter changes which could alleviate the occurrence of these anticipated wait times.

If you would like to discuss this potential job submission parameter changes you can respond to this message and we will follow up with more details.

Best regards,

{analyst}
Compute Canada Support


Additional job info:
  Current jobs: {num_jobs}
  Submitters:   {submitters}
');

INSERT INTO templates_content (template, label, language, title, body) VALUES (
  'impossible', 'impossible', 'fr',
  'AVIS: Vos calculs sur {cluster} peuvent être optimisés',
  'Bonjour {piName},

Nos enregistrements montrent que votre compte ''{account}'' a une quantité de ressources en attente dans la file d''attente des travaux sur {cluster} qui pourrait connaître un temps d''attente substantiel. Après examen de votre historique d''emploi récent, nous avons appris qu''il pourrait y avoir des changements dans les paramètres de soumission des emplois qui pourraient réduire l''occurrence de ces temps d''attente prévus.

Si vous souhaitez discuter de ces modifications potentielles des paramètres de soumission de travail, vous pouvez répondre à ce message et nous vous donnerons plus de détails. 

Meilleures salutations,

{analyst}
Compute Canada Support


Info additionel au tâches:
  Tâches au courant:   {num_jobs}
  Emetteurs de tâches: {submitters}
');

INSERT INTO templates (name) VALUES ('rac');
INSERT INTO templates_content (template, label, language, title, body) VALUES (
  'rac', 'rac', 'en',
  'NOTICE: Your computations on {cluster} may indicate a need for an ongoing allocation',
  'Hello {piName},

Our records show that your account ''{account}'' has a quantity of resources waiting in the job queue on {cluster} which could experience substantial wait time. Upon inspection of your recent job history it has come to our attention that your account''s recent usage is already above the expected usage rate of the account type. If it is anticipated that the account should be able to sustain greater that it is currently experiencing we recommend that the workload be distributed across multiple Compute Canada systems or that you apply for increased resource access via the Resource Allocation Competition (RAC) in future call of the program.

If you would like to discuss these potential options for increasing the sustained throughput of your projects at Compute Canada you can respond to this message and we will follow up with more details.

Best regards,

{analyst}
Compute Canada Support


Additional job info:
  Current jobs: {num_jobs}
  Submitters:   {submitters}
');

INSERT INTO templates_content (template, label, language, title, body) VALUES (
  'rac', 'rac', 'fr',
  'AVIS: Vos calculs sur {cluster} peuvent indiquer la nécessité d''une allocation continue',
  'Bonjour {piName},

Nos archives montrent que votre compte ''{account}'' a une quantité de ressources en attente dans la file d''attente des tâches sur {cluster} qui pourrait connaître un temps d''attente substantiel. Après examen de l''historique de vos travaux récents, nous avons constaté que l''utilisation récente de votre compte est déjà supérieure au taux d''utilisation prévu du type de compte. Si l''on prévoit que le compte devrait être en mesure de se maintenir plus longtemps que ce qu''il connaît actuellement, nous vous recommandons de répartir la charge de travail sur plusieurs systèmes de Calcul Canada ou de demander un accès accru aux ressources via le concours d''allocation de ressources (RAC) lors d''un prochain appel de le programme.

Si vous souhaitez discuter de ces options potentielles pour augmenter le débit soutenu de vos projets chez Compute Canada, vous pouvez répondre à ce message et nous vous donnerons plus de détails.

Meilleures salutations, 

{analyst}
Compute Canada Support


Info additionel au tâches:
  Tâches au courant:   {num_jobs}
  Emetteurs de tâches: {submitters}
');

INSERT INTO templates (name) VALUES ('empty');
INSERT INTO templates_content (template, label, language, title, body) VALUES (
  'empty', 'empty', 'en', 'Regarding your computations on {cluster}',
  'Hello {piName},



If you would like to discuss this issue with {account} you can respond to this message and we will follow up with more details.

Best regards,

{analyst}
Compute Canada Support


Additional job info:
  Current jobs: {num_jobs}
  Submitters:   {submitters}
');

INSERT INTO templates_content (template, label, language, title, body) VALUES (
  'empty', 'empty', 'fr', 'Vos calculs sur {cluster}',
  'Bonjour {piName},




Si vous souhaitez discuter de ce changement de priorité transitoire potentiel vers{ account}, vous pouvez répondre à ce message et nous vous donnerons plus de détails.

Meilleures salutations,

{analyst}
Compute Canada Support


Info additionel au tâches:
  Tâches au courant:   {num_jobs}
  Emetteurs de tâches: {submitters}
');

INSERT INTO appropriate_templates VALUES ('bursts', 'impossible', TRUE);
INSERT INTO appropriate_templates VALUES ('bursts', 'rac', TRUE);
INSERT INTO appropriate_templates VALUES ('bursts', 'candidate', TRUE);
INSERT INTO appropriate_templates VALUES ('oldjobs', 'impossible', TRUE);

INSERT INTO notifiers (name, type, config) VALUES ('Test Notifier', 'test', '{}');
