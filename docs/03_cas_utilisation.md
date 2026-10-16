# 03 — Cas d'utilisation métier

> **Objectif de ce document** : lister précisément chaque action que l'outil permet, avec ses
> conditions, son déroulement normal, ses cas d'erreur et son résultat. Chaque cas d'utilisation
> deviendra **un cas d'usage dans la couche Application** et **au moins un test**.

## Comment lire une fiche

| Rubrique | Sens |
|---|---|
| **Acteur** | Qui déclenche l'action |
| **Préconditions** | Ce qui doit être vrai avant (sinon l'action est refusée) |
| **Scénario nominal** | Le déroulement normal, étape par étape |
| **Variantes / erreurs** | Ce qui se passe quand ça ne se passe pas comme prévu |
| **Postconditions** | Ce qui est vrai après |
| **Règles métier** | Les règles fiscales ou de gestion appliquées, avec leur source |

## Vue d'ensemble

```
                         ┌──────────────────── OptiFisc ─────────────────────┐
                         │  Cœur métier                                      │
  Collaborateur ────────▶│   UC01 Importer et lire une balance               │
        │                │   UC02 Analyser les retraitements de l'IS         │
        │                │   UC03 Simuler un scénario d'optimisation         │
        │                │   UC04 Valider et générer les livrables  ◀────────┼──── Expert-comptable
        │                │                                                   │          │
        │                │  Préparation et pilotage                          │          │
        ├───────────────▶│   UC05 Gérer les dossiers clients                 │          │
        ├───────────────▶│   UC06 Renseigner les hypothèses de projection    │          │
        ├───────────────▶│   UC07 Calculer l'IS prévisionnel                 │          │
        ├───────────────▶│   UC08 Piloter les acomptes d'IS                  │          │
        ├───────────────▶│   UC09 Interroger l'assistant CGI  ───────────────┼──▶ OpenRouter
        ├───────────────▶│   UC14 Obtenir les propositions de l'agent IA ────┼──▶ OpenRouter
        │                │                                                   │          │
        │                │  Gouvernance                                      │          │
        │                │   UC10 Valider une règle du référentiel  ◀────────┼──────────┤
        │                │   UC11 Consulter la piste d'audit     ◀───────────┼──────────┤
  Tous ─────────────────▶│   UC12 S'authentifier                             │          │
  Administrateur ───────▶│   UC13 Gérer les utilisateurs et attributions     │          │
                         └───────────────────────────────────────────────────┘
```

**Priorité MVP** : P1 = indispensable à la soutenance · P2 = important · P3 = si le temps le permet.

| UC | Nom | Acteur principal | Priorité |
|---|---|---|---|
| UC01 | Importer et lire une balance | Collaborateur | P1 |
| UC02 | Analyser les retraitements de l'IS | Collaborateur | P1 |
| UC03 | Simuler un scénario d'optimisation | Collaborateur | P1 |
| UC04 | Valider et générer les livrables | Expert-comptable | P1 |
| UC05 | Gérer les dossiers clients | Collaborateur | P1 |
| UC06 | Renseigner les hypothèses de projection | Collaborateur | P1 |
| UC07 | Calculer l'IS prévisionnel | Collaborateur | P1 |
| UC08 | Piloter les acomptes d'IS | Collaborateur | P2 |
| UC09 | Interroger l'assistant CGI | Tous | P2 |
| UC10 | Valider une règle du référentiel | Expert-comptable | P2 |
| UC11 | Consulter la piste d'audit | Expert, Collaborateur | P2 |
| UC12 | S'authentifier | Tous | P1 |
| UC13 | Gérer les utilisateurs et attributions | Administrateur | P2 |
| UC14 | Obtenir les propositions de l'agent IA | Collaborateur, Expert | P1 (construit en dernier, J11) |

---

## UC01 — Importer et lire une balance

- **Acteur** : Collaborateur (ou Expert).
- **Préconditions** : connecté ; dossier ouvert, qui lui est attribué ; état `BROUILLON` ou `EN PRÉPARATION`.
- **Scénario nominal** :
  1. Le collaborateur dépose un fichier `.xlsx`, `.xls` ou `.csv` et indique la **date d'arrêté** (ex. 30/06/2026).
  2. Le système repère la ligne d'en-tête, puis les colonnes compte, intitulé et montants (4, 6 ou 8 colonnes, ou solde signé).
  3. Il convertit chaque montant en `Decimal`, en reconnaissant le format français (`1 234 567,89`).
  4. Il ignore les lignes de titre, les lignes de total et les comptes de regroupement (ex. `60` quand `601100` existe).
  5. Il lance les **contrôles** : équilibre débit = crédit, présence des classes 6 et 7, chiffre d'affaires créditeur.
  6. Il affiche un **rapport de lecture** : colonnes utilisées, nombre de comptes, lignes ignorées, résultats des contrôles.
  7. Le collaborateur **confirme**. La balance est enregistrée dans le dossier et le dossier passe `EN PRÉPARATION`.
- **Variantes / erreurs** :
  - *E1* Aucune colonne « Compte » trouvée → message expliquant les formats acceptés ; rien n'est enregistré.
  - *E2* Montants illisibles → listés ligne par ligne, avec le choix « corriger le fichier » ou « continuer (comptés pour 0) ».
  - *E3* Balance déséquilibrée → avertissement **non bloquant**, avec l'écart affiché.
  - *E4* Fichier protégé ou endommagé → message conseillant de réenregistrer en `.xlsx` ou d'exporter en CSV.
  - *V1* Une balance existe déjà → le système demande confirmation du remplacement ; l'ancienne est conservée dans l'historique.
- **Postconditions** : le dossier contient une `Balance` immuable, sa date d'arrêté et son rapport de lecture ; l'import est tracé.
- **Règles métier** : SYSCOHADA révisé (classes 1 à 8) ; le solde est débit − crédit ; les comptes sont comparés par **préfixe** (`647` couvre `6471`).
- **Réutilisation** : logique du lecteur de balance de la V2, convertie en `Decimal`.

## UC02 — Analyser les retraitements de l'IS

- **Acteur** : Collaborateur.
- **Préconditions** : balance importée (UC01) ; hypothèses de projection renseignées (UC06).
- **Scénario nominal** :
  1. Le système applique chaque règle de `retraitements.yaml` à la balance **projetée**.
  2. Les règles **automatiques** sont calculées depuis la balance :
     - `totalite` : tout le solde des comptes (ex. IS comptabilisé, compte 89, art. 35 ; amendes, compte 647, art. 36) ;
     - `plafond_ca` : la part au-delà d'un pourcentage du CA (ex. dons au-delà de 1 ‰ du CA HT, art. 32-1) ;
     - `plafond_ebe` : les intérêts nets au-delà de 30 % du résultat avant impôt, intérêts et dotations (art. 25-3).
  3. Les règles **à saisie** affichent une question et l'endroit où trouver l'information (« Grand livre 658, avis CNSS »). Le collaborateur saisit un montant ou « néant ».
  4. Le système classe les retraitements en 4 catégories : *non déductibles*, *plafonnées*, *conditions non remplies*, *déductions*.
  5. Pour chaque ligne, il affiche la base, le plafond, le montant retenu, l'article et la formule.
  6. Il signale à part les **sanctions hors résultat** (ex. droit de timbre de 1 % sur les paiements en espèces ≥ 100 000 FCFA, art. 21 et 423-4).
- **Variantes / erreurs** :
  - *V1* Une règle porte le statut `à valider` → elle est appliquée, mais marquée d'un badge « règle non validée par le cabinet ».
  - *V2* Une saisie reste vide → considérée « non renseignée », ce qui est différent de « néant ». Le dossier ne pourra pas être soumis à validation tant qu'une règle reste non renseignée.
  - *E1* Un paramètre manque au référentiel (ex. taux BCEAO non renseigné, art. 25-2) → la règle concernée est désactivée avec un message explicite ; le calcul ne plante pas.
- **Postconditions** : le dossier contient la liste des `LigneRetraitement` (montant, base, article, catégorie, origine automatique ou saisie).
- **Règles métier** : CGI art. 15 à 43 ; la liste exacte vient du référentiel (28 règles reprises de la V2, toutes au statut « à valider » au départ).

## UC03 — Simuler un scénario d'optimisation

- **Acteur** : Collaborateur.
- **Préconditions** : IS prévisionnel calculé (UC07).
- **Scénario nominal** :
  1. Le système affiche la **position de départ** : IS de droit commun, minimum de perception, IS dû, seuil de bascule.
  2. Il présente les leviers activables avant la clôture, chacun avec ses **conditions légales** sous forme de cases à cocher :
     - L01 amortissement dégressif d'un matériel neuf (art. 40) ;
     - L02 amortissement accéléré (art. 39) ;
     - L03 provision justifiée (art. 41) ;
     - L04 utilisation de la marge de déduction des dons (art. 32) ;
     - L05 charges anticipées nécessaires (art. 20 et 23-2).
  3. Le collaborateur paramètre un ou plusieurs leviers (montant, durée, mois d'acquisition…).
  4. Le **moteur déterministe** recalcule l'IS avec ces leviers et affiche, côte à côte, *avant* et *après* : résultat fiscal, IS dû, gain, et nature du gain (**économie définitive** ou simple **décalage d'impôt**).
  5. Si le dossier est au **minimum de perception**, le système l'explique : réduire le résultat sous le seuil de bascule ne réduit pas l'impôt, donc le gain est nul.
  6. Le collaborateur peut demander à l'**agent IA** des propositions complémentaires (UC14). Les propositions acceptées apparaissent ici comme des leviers déjà paramétrés.
  7. Le collaborateur **retient** un scénario. Il est enregistré avec ses paramètres et repris dans la note.
- **Variantes / erreurs** :
  - *V1* Une condition légale n'est pas cochée → le levier est calculé à titre indicatif mais marqué « conditions non remplies » ; il ne peut pas être retenu.
  - *V2* Plusieurs scénarios sont comparés → on peut en enregistrer 3 au maximum par dossier, dont un seul est retenu.
- **Postconditions** : un `Scenario` immuable (leviers, paramètres, résultat avant/après) est rattaché au dossier.
- **Règle d'or** : **l'IA propose, le moteur chiffre, l'humain décide.** Aucun montant affiché ne vient de l'IA (voir UC14).

## UC04 — Valider et générer les livrables

- **Acteur** : Expert-comptable (le collaborateur peut générer des versions **provisoires**).
- **Préconditions** : dossier `À VALIDER` (soumis par le collaborateur) ; toutes les règles à saisie renseignées.
- **Scénario nominal** :
  1. L'expert ouvre le dossier et voit un **résumé de contrôle** : IS dû, régime appliqué, retraitements les plus importants, règles non validées utilisées, scénario retenu, alertes.
  2. Il peut descendre jusqu'à la piste d'audit de chaque montant.
  3. Il **valide**, ou **renvoie** avec un commentaire obligatoire (le dossier repasse alors `EN PRÉPARATION`).
  4. À la validation, le système **fige** le résultat : montants, version du référentiel, scénario, date et nom du valideur.
  5. L'expert génère les livrables définitifs :
     - **Note de pilotage** (Word, modifiable) : synthèse, IS prévisionnel, leviers, acomptes, réserves ;
     - **Dossier de calcul** (Excel) : tableau de passage avec totaux en **formules**, balance projetée, hypothèses, piste d'audit ;
     - **Projet de lettre au DGI** (Word), si une réduction d'acomptes est retenue (UC08).
  6. Le dossier passe `LIVRÉ`.
- **Variantes / erreurs** :
  - *V1* Des règles « à valider » ont été utilisées → la validation reste possible, mais l'expert doit cocher « J'ai vérifié les règles non validées », et la note mentionne ces réserves.
  - *V2* Livrable provisoire (collaborateur) → filigrane « PROJET — non validé », sans nom de valideur.
- **Postconditions** : résultat figé ; fichiers générés dans `var/livrables/<dossier>/` ; empreinte (hash) de chaque fichier enregistrée dans la piste d'audit.

---

## UC05 — Gérer les dossiers clients

- **Acteur** : Collaborateur, Expert.
- **Scénario** : créer un dossier (raison sociale, IFU facultatif, secteur pour le minimum de perception : `autres`, `btp` ou `immobilier`, catégorie de taux : 30 % ou 25 %, exercice), l'ouvrir, le lister ou l'archiver.
- **Règles** : un dossier = un client × un exercice. Le secteur et la catégorie de taux sont des **choix fermés** (listes), jamais du texte libre interprété.

## UC06 — Renseigner les hypothèses de projection

- **Acteur** : Collaborateur.
- **Scénario** : saisir le coefficient d'activité du reste de l'année (1 = même rythme), les ajustements de fin d'année (dotations aux amortissements non encore passées, charges connues), l'IS N-1 (base des acomptes), l'AIB imputable et les déficits antérieurs reportables.
- **Règles** : projection = réalisé + réalisé ÷ mois écoulés × mois restants × coefficient ; seuls les comptes de gestion (classes 6, 7, 8) sont projetés ; l'IS comptabilisé (89) n'est pas projeté. Alerte si la balance est arrêtée avant fin mars (projection fragile).

## UC07 — Calculer l'IS prévisionnel

- **Acteur** : Collaborateur.
- **Scénario** : résultat comptable projeté → + réintégrations − déductions (UC02) → − déficits antérieurs (art. 43) → résultat fiscal → IS de droit commun (art. 46) → minimum de perception (art. 47) → IS dû = maximum des deux → + redevance ORTB (art. 47-6). Le système affiche aussi le seuil de bascule et les alertes.
- **Postconditions** : `ResultatFiscal` immuable avec sa piste d'audit numérotée ; dossier `CALCULÉ`.
- **Tests de référence** : les deux balances de démonstration (BATI-PLUS BTP, NOVA SERVICES), dont les résultats ont été calculés à la main dans la V2.

## UC08 — Piloter les acomptes d'IS

- **Acteur** : Collaborateur.
- **Scénario** : échéancier des 4 acomptes (10 mars, 10 juin, 10 septembre, 10 décembre ; 25 % de l'IS N-1, art. 51) ; détection d'un **surpaiement** prévisible ; si les délais le permettent (demande au DGI 30 jours avant l'échéance, art. 52), calcul de l'acompte réduit avec une marge de prudence choisie par le cabinet ; rappel du risque (pénalité de 20 % si l'écart dépasse 10 %, art. 52-7). Si c'est trop tard, l'excédent est signalé comme crédit d'impôt.
- **Règle** : la date du jour est fournie par le port `Horloge`, pour que le calcul soit testable.

## UC09 — Interroger l'assistant CGI

- **Acteur** : Tous.
- **Scénario** :
  1. L'utilisateur pose une question sur la loi (ex. « Quel est le plafond de déduction des cadeaux publicitaires ? »).
  2. Le contrôle du **pare-feu de données** avertit si la question semble contenir une donnée client.
  3. La recherche BM25 renvoie les 5 articles les plus pertinents (CGI 2026, LPF 2024), en priorité ceux du chapitre IS. Les articles s'affichent **immédiatement**, avant toute IA.
  4. Si l'IA est activée, le système envoie la question et ces articles seulement à OpenRouter, avec la consigne de répondre **uniquement** à partir d'eux et de citer les articles.
  5. La réponse s'affiche avec la mention « Proposition générée par IA, à vérifier dans les articles ci-dessus ».
- **Variantes** : IA désactivée ou indisponible (pas d'internet) → seuls les articles sont affichés ; la réponse ne cite aucun article fourni → elle est marquée « non sourcée ».
- **Postconditions** : l'appel est journalisé (utilisateur, modèle, question, articles, durée). Aucune donnée de dossier n'est transmise.

## UC10 — Valider une règle du référentiel

- **Acteur** : Expert-comptable.
- **Scénario** : consulter une règle (texte, article, comptes, formule) ; la voir appliquée à un **cas chiffré** ; la valider avec un commentaire, ou la remettre « à valider ».
- **Règles** : la validation est rattachée à la **version** du fichier de règles. Si le YAML change, les règles modifiées repassent automatiquement « à valider ».

## UC11 — Consulter la piste d'audit

- **Acteur** : Expert (tous dossiers), Collaborateur (ses dossiers), Administrateur.
- **Scénario** : chronologie des événements d'un dossier (import, saisies, calculs, scénarios, soumission, validation, livrables, appels à l'IA), avec un filtre par type ; export Excel.

## UC12 — S'authentifier

- **Acteur** : Tous.
- **Scénario** : e-mail + mot de passe → vérification de l'empreinte → ouverture de session. Changement obligatoire à la première connexion. Blocage après 5 échecs ; déconnexion après 30 minutes d'inactivité (doc 02, §5.3).

## UC13 — Gérer les utilisateurs et attributions

- **Acteur** : Administrateur (attribution aussi possible par l'expert).
- **Scénario** : créer un compte (mot de passe initial aléatoire), changer un rôle, désactiver un compte, attribuer un dossier à un collaborateur.

## UC14 — Obtenir les propositions de l'agent IA

> Ajouté le 14/10/2026 (décision D3.2). Besoin exprimé : l'IA doit pouvoir **analyser le dossier et
> proposer des axes d'optimisation**, y compris ceux que le collaborateur aurait omis, en s'appuyant
> sur la réglementation. Elle n'est donc pas un simple moteur de recherche : c'est un **agent**, qui
> raisonne et choisit lui-même quels outils utiliser.

- **Acteur** : Collaborateur ou Expert.
- **Préconditions** : IS prévisionnel calculé (UC07) ; IA activée ; règles d'envoi respectées (doc 01, A.3).
- **Ce qu'est l'agent** : un LLM à qui l'on donne une **mission** et une **boîte à outils**. À chaque
  tour, il choisit un outil, lit le résultat, puis décide de la suite. Le nombre de tours est limité.
  Les outils sont des fonctions **écrites et contrôlées par nous** : l'agent ne peut rien faire
  d'autre que ce qu'ils permettent.

  | Outil donné à l'agent | Ce qu'il fait | Ce qu'il renvoie à l'agent |
  |---|---|---|
  | `lire_profil_dossier` | Construit un **profil pseudonymisé** du dossier | Secteur, taux, mois d'arrêté, agrégats **arrondis au million** (CA, résultat, totaux par catégorie de retraitement), position par rapport au seuil de bascule, leviers déjà simulés. Ni nom, ni IFU, ni libellé de compte. |
  | `rechercher_articles` | Recherche BM25 dans le CGI et le LPF | Numéros et textes d'articles |
  | `lister_leviers` | Catalogue des leviers L01 à L05 et de leurs conditions | Identifiants, conditions, articles |
  | `simuler_levier` | **Appelle le moteur déterministe** avec des paramètres | Gain arrondi et nature du gain (économie ou décalage) |
  | `proposer` | Enregistre une proposition | Accusé de réception |

- **Scénario nominal** :
  1. L'utilisateur clique sur « Demander des propositions » (écran E10).
  2. L'agent lit le profil, consulte les articles utiles, simule les leviers pertinents.
  3. Il produit **3 à 5 propositions**, chacune d'un de ces deux types :
     - **Levier chiffré** : un levier du catalogue, avec des paramètres. Le montant affiché est
       **recalculé par le moteur** dans l'application, jamais recopié du texte de l'IA.
     - **Piste à étudier** : un axe hors catalogue (ex. une exonération, un régime, un point de
       procédure), avec l'article et le raisonnement, **sans aucun chiffre**.
  4. Chaque proposition affiche : titre, article(s), justification, type, statut « à examiner ».
  5. L'utilisateur **accepte** ou **écarte** chaque proposition (motif obligatoire pour écarter).
     - Levier accepté → il devient un scénario paramétré dans UC03.
     - Piste acceptée → elle figure dans la note comme « point à examiner par le cabinet ».
- **Rôle du modèle de décision (Jev, « Système 1 », doc 01 A.4)** :
  - *avant* l'agent : pré-tri des leviers du catalogue (`noul` « ce levier est-il pertinent pour ce profil ? ») ;
  - *après* l'agent : jugement de chaque proposition (`noul` « étayée par l'article cité ? », `score` « niveau de risque » de 1 à 4) ;
  - sous le seuil de confiance (0,90 au départ, à ajuster sur les dossiers de démo), la proposition porte le badge « confiance faible — vérifier en priorité » ;
  - si Jev est indisponible, l'agent fonctionne sans pré-tri ni jugement, avec un message.
- **Garde-fous vérifiés par le code (et non par la consigne donnée à l'IA)** :
  - un article cité qui **n'existe pas** dans le corpus → proposition rejetée automatiquement ;
  - les nombres écrits par l'IA dans sa justification sont **masqués** à l'affichage ; seuls les
    montants du moteur apparaissent ;
  - 10 appels d'outils au maximum et 90 secondes au maximum ; au-delà, on affiche les propositions déjà produites ;
  - le profil envoyé est contrôlé par un test : il ne doit contenir ni raison sociale, ni IFU, ni libellé ;
  - tout est journalisé : profil envoyé, outils appelés, propositions, décisions.
- **Variantes / erreurs** :
  - *E1* IA indisponible ou délai dépassé → message « Propositions indisponibles » ; le reste de l'outil fonctionne.
  - *E2* Réponse illisible (format attendu non respecté) → une nouvelle tentative, puis E1.
  - *V1* Dossier réel et fournisseur non confidentiel → l'agent refuse de s'exécuter (doc 01, A.3).
- **Postconditions** : `Proposition[]` immuables rattachées au dossier, chacune avec sa décision humaine.
- **Règle d'or** : **l'IA propose, le moteur chiffre, l'humain décide.**

---

## Traçabilité : du cas d'utilisation au code

| UC | Cas d'usage (Application) | Objets du domaine principaux |
|---|---|---|
| UC01 | `ImporterBalance` | `Balance`, `LigneBalance`, `RapportLecture` |
| UC02 | `AnalyserRetraitements` | `RegleRetraitement`, `LigneRetraitement` |
| UC03 | `SimulerScenario`, `RetenirScenario` | `Levier`, `EffetLevier`, `Scenario` |
| UC04 | `SoumettreDossier`, `ValiderDossier`, `RenvoyerDossier`, `GenererLivrables` | `Dossier`, `EtatDossier`, `ResultatFige` |
| UC05 | `CreerDossier`, `ListerDossiers` | `Dossier`, `Secteur`, `CategorieTaux` |
| UC06 | `DefinirHypotheses` | `HypothesesProjection` |
| UC07 | `CalculerIsPrevisionnel` | `ResultatFiscal`, `LigneAudit` |
| UC08 | `EtablirEcheancierAcomptes` | `Echeancier`, `RecommandationAcompte` |
| UC09 | `RepondreQuestionFiscale` | `Article`, `ReponseAssistant` |
| UC10 | `ValiderRegle` | `ValidationRegle` |
| UC11 | `ConsulterJournal` | `EvenementAudit` |
| UC12 | `Connecter`, `ChangerMotDePasse` | `Utilisateur`, `Role` |
| UC13 | `CreerUtilisateur`, `AttribuerDossier` | `Utilisateur`, `Attribution` |
| UC14 | `DemanderPropositions`, `DeciderProposition` | `ProfilPseudonymise`, `Proposition`, `DecisionProposition` |

---

## Décisions à valider

- [ OUI ] **D3.1** Liste des 13 cas d'utilisation et leurs priorités P1 / P2.
- [ ✔ Révisé le 14/10 → UC14 ajouté, UC03 ajusté. Commentaire d'origine : En vrais le role de l'ia selon les besoin de celui pour qui je realise l'app est que l'ia soit en mesure de faire des proposition apres analyse et toi en se basant sur la reglementation afin de pouvoire évantuellement couvrire des axe d'optiisation omis , au fond l'ia ou l'agent ia qui travayera ne sera pas just deterministe et s'aura reagire c'est evantuelement our cela que j'ai penser a laya (semblable a jev) pour ce genre de prise de decision  ] **D3.2** UC03 reformulé : la simulation est **déterministe** ; l'assistant IA sert seulement à consulter les articles cités. Est-ce conforme à ton intention pour « simuler avec l'assistant IA » ?
- [ OUI ] **D3.3** Distinction « non renseigné » / « néant » pour les saisies, bloquante pour la soumission.
- [ OUI (paut etre ameliorer ou évoluer au besoin) ] **D3.4** 28 règles de la V2 reprises comme base du référentiel, toutes « à valider » au départ.
- [ OUI/Ameliorable au besoin ] **D3.5** Les leviers L01 à L05, plus la réduction d'acomptes (UC08), constituent le périmètre d'optimisation du MVP.
- [ OUI ] **D3.6** (nouveau) Agent IA à outils (UC14) : deux types de propositions (levier chiffré par le moteur / piste à étudier sans chiffre), décision humaine sur chaque proposition, garde-fous contrôlés par le code.
- [ OUI ] **D3.7** (nouveau) Agent écrit **sans framework d'agent** (boucle simple de 50 à 80 lignes dans la couche Application), pour que tu comprennes chaque étape. Un framework (LangGraph, etc.) reste une perspective.
- [ ✔ Révisé le 16/10 → le juge est notre code déterministe (`JugeDeterministe`), pas Jev ; voir doc 01 A.4. Commentaire d'origine : « Comme je l'est dit en D1.8 » ] **D3.8** (nouveau) Jev comme pré-tri et juge des propositions de l'agent, avec un seuil de confiance ; il ne décide jamais à la place de l'humain.
