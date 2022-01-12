PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
INSERT INTO clusters VALUES('testcluster','Test Cluster');
INSERT INTO clusters VALUES('testcluster2','Test Cluster 2');
INSERT INTO components VALUES('testcluster_scheduler','Scheduler','testcluster','scheduler');
INSERT INTO components VALUES('testcluster_detector','Detector','testcluster','detector');
INSERT INTO components VALUES('testcluster2_scheduler','Scheduler','testcluster2','scheduler');
INSERT INTO components VALUES('testcluster2_detector','Detector','testcluster2','detector');
INSERT INTO apikeys VALUES('testapikey_d','WuHheVDysQQwdb+NK98w8EOHdiNUjLlz2Uxg/kIHqIGOek4DAmC5NCd2gZv7RQ==','testcluster_detector',1628178497,'a');
INSERT INTO apikeys VALUES('testapikey_s','T3h5mwEk7mrVwxdon+s9blWhVh8zHDd7PVoUoWJsTf5Qd2EUie6I4pdBuyRykw==','testcluster_scheduler',1628178497,'a');
INSERT INTO apikeys VALUES('fakeyfakefake','ZoHCik4dOZm4VvKnkQUv9lcWydR8aH4bNCW2/fwxGGOfbj5SrBAY50nD3gNCIA==','testcluster_detector',NULL,'d');
INSERT INTO apikeys VALUES('testapikey2_d','rammarammadingdong','testcluster2_detector',NULL,'a');
INSERT INTO apikeys VALUES('testapikey2_s','GEMr1Ksi7I9G9BXuAhY4IITgMcyAKmHzgjFZ2uBTUpQkT1n3xUda5v+4FQAaBA==','testcluster2_scheduler',1628178495,'a');
INSERT INTO notifiers VALUES('Test Notifier','test','{}');
INSERT INTO templates VALUES('other language follows','fr',replace('\n(La version française de ce message suit.)\n','\n',char(10)));
INSERT INTO templates VALUES('other language follows','en',replace('\n(The English language version of this message follows.)\n','\n',char(10)));
INSERT INTO templates VALUES('separator','',replace('\n--------------------------------------\n','\n',char(10)));
INSERT INTO templates VALUES('intro title','en','NOTICE: Your computations on %cluster% may be eligible for prioritised execution');
INSERT INTO templates VALUES('intro title','fr','AVIS: Vos calculs à %cluster% peuvent être éligibles pour une exécution prioritaire');
INSERT INTO templates VALUES('intro','en',replace('Hello %piName%,\n\nOngoing analysis of queued jobs on %cluster% has shown that your project has a quantity of jobs that would benefit from a temporary escalation in priority.  Please let us know by replying to this message if you are interested.\n\nAdditional job info:\n  Current jobs: %num_jobs%\n  Submitters:   %submitters%\n\nBest regards,\n%analyst%','\n',char(10)));
INSERT INTO templates VALUES('intro','fr',replace('Bonjour %piName%,\n\nAnalyse en cours des travaux en attente sur %cluster% a montré que votre projet comporte une quantité de tâches bénéficier d''une escalade temporaire en priorité. S''il vous plaît laissez-nous savoir par répondre à ce message si vous êtes intéressé.\n\nInfo additionel au tâches:\n  Tâches au courant:   %num_jobs%\n  Emetteurs de tâches: %submitters%\n\nMeilleures salutations,\n%analyst%','\n',char(10)));
INSERT INTO templates VALUES('candidate title','en','NOTICE: Your computations on %cluster% may be eligible for prioritised execution');
INSERT INTO templates VALUES('candidate','en',replace('Hello %piName%,\n\nOur records show that your account ''%account%'' has a quantity of resources waiting in the job queue on %cluster% which could experience substantial wait time. Considering this pending work load along with the account''s recent usage history we may be able to provide a transient increase of priority to decrease these anticipated wait times.\n\nIf you would like to discuss this potential transient priority change to %account% you can respond to this message and we will follow up with more details.\n\nBest regards,\n\n%analyst%\nCompute Canada Support\n\n\nAdditional job info:\n  Current jobs: %num_jobs%\n  Submitters:   %submitters%\n','\n',char(10)));
INSERT INTO templates VALUES('candidate title','fr','AVIS: Vos calculs sur %cluster% peuvent être éligibles pour une exécution prioritaire');
INSERT INTO templates VALUES('candidate','fr',replace('Bonjour %piName%,\n\nNos archives montrent que votre compte ''% account%'' a une quantité de ressources en attente dans la file d''attente des tâches sur %cluster% qui pourrait connaître un temps d''attente substantiel. Compte tenu de cette charge de travail en attente ainsi que de l''historique d''utilisation récent du compte, nous pourrions être en mesure de fournir une augmentation transitoire de la priorité pour réduire ces temps d''attente prévus.\n\nSi vous souhaitez discuter de ce changement de priorité transitoire potentiel vers% account%, vous pouvez répondre à ce message et nous vous donnerons plus de détails.\n\nMeilleures salutations,\n\n%analyst%\nCompute Canada Support\n\n\nInfo additionel au tâches:\n  Tâches au courant:   %num_jobs%\n  Emetteurs de tâches: %submitters%\n','\n',char(10)));
INSERT INTO templates VALUES('impossible title','en','NOTICE: Your computations on %cluster% may be optimized');
INSERT INTO templates VALUES('impossible','en',replace('Hello %piName%,\n\nOur records show that your account ''%account%'' has a quantity of resources waiting in the job queue on %cluster% which could experience substantial wait time. Upon inspection of your recent job history it has come to our attention that there may be job submission parameter changes which could alleviate the occurrence of these anticipated wait times.\n\nIf you would like to discuss this potential job submission parameter changes you can respond to this message and we will follow up with more details.\n\nBest regards,\n\n%analyst%\nCompute Canada Support\n\n\nAdditional job info:\n  Current jobs: %num_jobs%\n  Submitters:   %submitters%\n','\n',char(10)));
INSERT INTO templates VALUES('impossible title','fr','AVIS: Vos calculs sur %cluster% peuvent être optimisés');
INSERT INTO templates VALUES('impossible','fr',replace('Bonjour %piName%,\n\nNos enregistrements montrent que votre compte ''% account%'' a une quantité de ressources en attente dans la file d''attente des travaux sur %cluster% qui pourrait connaître un temps d''attente substantiel. Après examen de votre historique d''emploi récent, nous avons appris qu''il pourrait y avoir des changements dans les paramètres de soumission des emplois qui pourraient réduire l''occurrence de ces temps d''attente prévus.\n\nSi vous souhaitez discuter de ces modifications potentielles des paramètres de soumission de travail, vous pouvez répondre à ce message et nous vous donnerons plus de détails. \n\nMeilleures salutations,\n\n%analyst%\nCompute Canada Support\n\n\nInfo additionel au tâches:\n  Tâches au courant:   %num_jobs%\n  Emetteurs de tâches: %submitters%\n','\n',char(10)));
INSERT INTO templates VALUES('rac title','en','NOTICE: Your computations on %cluster% may indicate a need for an ongoing allocation');
INSERT INTO templates VALUES('rac','en',replace('Hello %piName%,\n\nOur records show that your account ''%account%'' has a quantity of resources waiting in the job queue on %cluster% which could experience substantial wait time. Upon inspection of your recent job history it has come to our attention that your account''s recent usage is already above the expected usage rate of the account type. If it is anticipated that the account should be able to sustain greater that it is currently experiencing we recommend that the workload be distributed across multiple Compute Canada systems or that you apply for increased resource access via the Resource Allocation Competition (RAC) in future call of the program.\n\nIf you would like to discuss these potential options for increasing the sustained throughput of your projects at Compute Canada you can respond to this message and we will follow up with more details.\n\nBest regards,\n\n%analyst%\nCompute Canada Support\n\n\nAdditional job info:\n  Current jobs: %num_jobs%\n  Submitters:   %submitters%\n','\n',char(10)));
INSERT INTO templates VALUES('rac title','fr','AVIS: Vos calculs sur %cluster% peuvent indiquer la nécessité d''une allocation continue');
INSERT INTO templates VALUES('rac','fr',replace('Bonjour %piName%,\n\nNos archives montrent que votre compte ''% account%'' a une quantité de ressources en attente dans la file d''attente des tâches sur %cluster% qui pourrait connaître un temps d''attente substantiel. Après examen de l''historique de vos travaux récents, nous avons constaté que l''utilisation récente de votre compte est déjà supérieure au taux d''utilisation prévu du type de compte. Si l''on prévoit que le compte devrait être en mesure de se maintenir plus longtemps que ce qu''il connaît actuellement, nous vous recommandons de répartir la charge de travail sur plusieurs systèmes de Calcul Canada ou de demander un accès accru aux ressources via le concours d''allocation de ressources (RAC) lors d''un prochain appel de le programme.\n\nSi vous souhaitez discuter de ces options potentielles pour augmenter le débit soutenu de vos projets chez Compute Canada, vous pouvez répondre à ce message et nous vous donnerons plus de détails.\n\nMeilleures salutations, \n\n%analyst%\nCompute Canada Support\n\n\nInfo additionel au tâches:\n  Tâches au courant:   %num_jobs%\n  Emetteurs de tâches: %submitters%\n','\n',char(10)));
INSERT INTO templates VALUES('empty title','en','Regarding your computations on %cluster%');
INSERT INTO templates VALUES('empty','en',replace('Hello %piName%,\n\n\n\nIf you would like to discuss this issue with %account% you can respond to this message and we will follow up with more details.\n\nBest regards,\n\n%analyst%\nCompute Canada Support\n\n\nAdditional job info:\n  Current jobs: %num_jobs%\n  Submitters:   %submitters%\n','\n',char(10)));
INSERT INTO templates VALUES('empty title','fr','Vos calculs sur %cluster%');
INSERT INTO templates VALUES('empty','fr',replace('Bonjour %piName%,\n\n\n\n\nSi vous souhaitez discuter de ce changement de priorité transitoire potentiel vers% account%, vous pouvez répondre à ce message et nous vous donnerons plus de détails.\n\nMeilleures salutations,\n\n%analyst%\nCompute Canada Support\n\n\nInfo additionel au tâches:\n  Tâches au courant:   %num_jobs%\n  Emetteurs de tâches: %submitters%\n','\n',char(10)));
INSERT INTO reportables VALUES(1,1628178495,1,'testcluster',NULL,NULL,NULL,'null');
INSERT INTO reportables VALUES(2,1628178496,4,'testcluster','tst-003',NULL,NULL,'null');
INSERT INTO reportables VALUES(3,1628178496,3,'testcluster','tst-003',NULL,NULL,'null');
INSERT INTO reportables VALUES(4,1628178497,5,'testcluster','tst-003',NULL,NULL,'{"thing": "thong"}');
INSERT INTO reportables VALUES(5,1628178497,2,'testcluster',NULL,NULL,NULL,'null');
INSERT INTO bursts VALUES(1,'p','def-pi1','c',0.0,1000,2000,'userQ');
INSERT INTO bursts VALUES(2,'p','def-dleske-aa','c',1.0,1005,3000,'userQ');
INSERT INTO bursts VALUES(3,'p','def-bobaloo-aa','c',1.5,1015,2015,'userQ userX');
INSERT INTO oldjobs VALUES(4,'def-dleske','userQ','c',123);
INSERT INTO oldjobs VALUES(5,'def-bobaloo-aa','userQ','c',612);
INSERT INTO history VALUES(1,2,'tst-003','2019-03-31 10:31 AM','Hey how are ya','{"datum": "state", "was": "pending", "now": "rejected"}');
INSERT INTO history VALUES(2,2,'tst-003','2019-03-31 10:35 AM','This is not the way','{"datum": "claimant", "was": null, "now": "tst-003"}');
INSERT INTO history VALUES(3,2,'tst-003','2019-03-31 10:37 AM','Reverting to &lt;b&gt;pending&lt;/b&gt;','{"datum": "state", "was": "rejected", "now": "pending"}');
INSERT INTO history VALUES(4,2,'tst-003','2019-03-31 10:32 AM','I just dinnae aboot this guy','null');
INSERT INTO history VALUES(5,3,'tst-003','2021-08-05 15:48:16','Stupid note','{"datum": "state", "was": "pending", "now": "rejected"}');
INSERT INTO history VALUES(6,3,'tst-003','2021-08-05 15:48:16','Reverting to pending again','{"datum": "state", "was": "rejected", "now": "pending"}');
INSERT INTO history VALUES(7,3,'tst-003','2021-08-05 15:48:16','This is not the way of the leaf','{"datum": "claimant", "was": null, "now": "tst-003"}');
INSERT INTO history VALUES(8,3,'tst-003','2021-08-05 15:48:16','I just do not ascertain this chap','null');
INSERT INTO history VALUES(9,4,'tst-003','2019-03-31 10:35 AM','This is not the way','{"datum": "claimant", "was": null, "now": "tst-003"}');
COMMIT;
