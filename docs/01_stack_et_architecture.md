# 01 — Stack technique et architecture

> **Objectif de ce document** : expliquer quels outils on utilise, pourquoi, et comment le code sera
> rangé. À la fin, tu dois pouvoir dire pour n'importe quel futur fichier : « il va dans telle couche,
> parce que… ».

---

## Partie A — La stack technique

### A.1 Vue d'ensemble

| Besoin | Outil retenu | Alternative écartée | Raison du choix |
|---|---|---|---|
| Langage | **Python 3.14** (version installée sur le poste ; 3.12 minimum) | — | Lisible pour un débutant, bibliothèques comptables et bureautiques mûres, déjà utilisé dans V1 et V2. |
| Interface | **Streamlit** | FastAPI + React | Un seul langage, pas de JavaScript, fonctionne dans le navigateur du poste. Suffisant pour quelques utilisateurs d'un cabinet. |
| Montants | **`decimal.Decimal`** (bibliothèque standard) | `float` | Exactitude au franc près (voir A.2). |
| Base de données | **SQLite** (module `sqlite3` standard) | PostgreSQL | Un seul fichier, aucun serveur à installer ou administrer en cabinet. |
| Règles fiscales | **Fichiers YAML** + validation **pydantic** | Règles écrites dans le code Python | Un comptable peut relire et faire valider une règle sans lire de Python. |
| Lecture des balances | **openpyxl** (Excel), **xlrd** (vieux .xls), **csv** (standard) | — | Formats réellement exportés par les logiciels comptables. Repris de la V2. |
| Livrables | **openpyxl** (Excel), **python-docx** (Word) | PDF | Le cabinet doit pouvoir **modifier** la note avant envoi. |
| Recherche dans le CGI | **BM25** (`rank_bm25`), en local | Base vectorielle (ChromaDB) | Environ 800 articles : une recherche par mots-clés locale suffit, sans serveur. |
| IA générative (« Système 2 ») | **OpenRouter, modèles gratuits** (suffixe `:free`), modèle choisi dans la configuration, derrière un *port* interchangeable | Ollama seul ; modèles payants | Choix validé. Voir A.3 pour les précautions de confidentialité. |
| Décision rapide (« Système 1 ») | **Juge déterministe écrit par nous** (`JugeDeterministe`), derrière le port `ModeleDecision` ; Jev ou Laya branchables plus tard | Jev (payant) ; Laya (à réentraîner) | Gratuit, instantané, et chaque score s'explique ligne par ligne. Voir A.4 (décision du 16/10/2026). |
| Tests | **pytest** | unittest | Syntaxe la plus simple, standard de fait. |
| Qualité du code | **ruff** (style et erreurs courantes) | — | Un seul outil, rapide, corrige automatiquement. |

Règle de sobriété : **toute nouvelle dépendance doit être justifiée dans ce tableau.** Chaque
bibliothèque ajoutée est du code qu'on ne maîtrise pas et qu'il faudra mettre à jour.

### A.2 Pourquoi `Decimal` et pas `float`

Un `float` est stocké en binaire, et beaucoup de nombres décimaux n'ont pas de représentation binaire
exacte :

```python
>>> 0.1 + 0.2
0.30000000000000004          # float : faux à la 17e décimale
>>> from decimal import Decimal
>>> Decimal("0.1") + Decimal("0.2")
Decimal('0.3')               # Decimal : exact
```

Sur un seul calcul, l'écart est invisible. Mais sur une balance de 500 comptes additionnés, multipliés
par des taux puis arrondis, les écarts peuvent faire basculer un arrondi au franc. Devant un jury
d'expertise comptable, **un tableau de passage dont le total ne tombe pas juste au franc ruine la
crédibilité de l'outil.**

Conventions fixées pour tout le projet :

1. **Un montant est toujours un `Decimal`**, créé à partir d'une **chaîne** (`Decimal("1500000")`) ou
   d'un entier. On ne fait jamais `Decimal(0.1)`, qui recopierait l'erreur du `float`.
2. **Les taux aussi** sont des `Decimal` (`Decimal("0.30")`), lus depuis le YAML sous forme de texte.
3. **On arrondit une seule fois, au franc**, à la fin de chaque ligne de calcul affichée, avec la
   règle de l'arrondi commercial (`ROUND_HALF_UP` : 0,5 arrondi au-dessus). Une fonction unique
   `arrondir_fcfa()` sera la seule autorisée à arrondir.
4. **Conversion aux frontières** : les bibliothèques Excel renvoient des `float`. Le lecteur de balance
   les convertit en `Decimal` **dès la lecture**. Après cette frontière, plus aucun `float` ne circule.
5. **En base**, les montants sont stockés en `TEXT` (ex. `"1500000"`), puis relus en `Decimal`. SQLite
   ne connaît pas le type décimal ; le stocker en `REAL` le transformerait en `float`.

### A.3 OpenRouter et confidentialité des données clients

**Le point de tension.** Les prototypes précédents imposaient « IA locale uniquement (Ollama) », pour
respecter le secret professionnel et la loi béninoise n° 2017-20 sur la protection des données
personnelles (contrôlée par l'APDP). OpenRouter est un **service en ligne** : tout ce qu'on lui envoie
quitte le cabinet et transite par un ou plusieurs fournisseurs, hors du Bénin.

**Pourquoi OpenRouter malgré tout (contexte du 14/10/2026).** En local, sans machine puissante, une
réponse prend environ 3 minutes et échoue parfois. De plus, le poste de la soutenance ne sera pas le
tien et n'aura pas Ollama. OpenRouter donne des réponses en quelques secondes, sans serveur à louer et
sans contrat direct avec un grand fournisseur. En production réelle, le cabinet hébergerait l'IA dans
un environnement confidentiel. Le port `FournisseurIA` permet ce changement sans toucher au métier.

**La solution : un « pare-feu de données » entre le dossier client et l'IA.**

Depuis l'ajout de l'agent de propositions (UC14), l'IA doit voir **une partie** du dossier. On
distingue donc trois niveaux de données :

| Niveau | Contenu | Envoyé à l'IA ? |
|---|---|---|
| **Public** | Question sur la loi, articles du CGI et du LPF | Oui |
| **Pseudonymisé** | Profil construit par le code : secteur, taux, mois d'arrêté, agrégats **arrondis au million**, position par rapport au seuil, gains simulés arrondis | Oui, uniquement à l'agent (UC14) |
| **Identifiant** | Raison sociale, IFU, noms de personnes, libellés de comptes (ils peuvent contenir des noms de fournisseurs), balance détaillée, notes, livrables | **Jamais** |

Concrètement :

1. **L'assistant CGI (UC09) répond sur la loi, pas sur le dossier.** Il ne reçoit que du « public ».
2. **L'agent (UC14) ne reçoit que du « pseudonymisé »**, fabriqué par une seule fonction,
   `construire_profil_pseudonymise()`. Un test vérifie qu'aucune donnée identifiante n'en sort.
3. **Garde-fou selon le type de dossier.** Chaque dossier est marqué *démonstration* ou *réel*, et
   chaque fournisseur d'IA est déclaré *confidentiel* ou non. Réglage par défaut : **OpenRouter n'est
   autorisé que pour les dossiers de démonstration.** Pour un dossier réel, l'agent refuse de
   s'exécuter, sauf si le cabinet active explicitement l'option (décision tracée), ou s'il utilise un
   fournisseur déclaré confidentiel.
4. **Les explications chiffrées propres au dossier** (« pourquoi le minimum de perception s'applique ici ? »)
   restent produites **sans IA**, par des modèles de phrases remplis par le moteur.
5. **Un contrôle de la question** affiche un avertissement si elle semble contenir une donnée client
   (nombre à plus de 5 chiffres, nom d'un client connu). Ce contrôle est imparfait : il complète la
   règle d'usage, il ne la remplace pas.
6. **Le fournisseur d'IA est un port.** Adaptateurs prévus : `OpenRouter` (par défaut), `IADesactivee`
   (l'application marche sans IA), et plus tard `Ollama` ou un hébergement confidentiel.
7. **La clé d'API** est lue dans un fichier `.env` (ou dans les secrets de l'hébergeur en ligne),
   jamais dans le code.
8. **Chaque appel à l'IA est journalisé** : qui, quand, quel modèle, ce qui a été envoyé, ce qui est revenu.

> À exposer dans le mémoire : ce choix est un **arbitrage** entre la qualité des modèles en ligne et la
> confidentialité. Le pare-feu de données en est la réponse d'architecture.

### A.4 Laya et Jev : des modèles de décision (« Système 1 »)

Sources fournies le 14/10/2026 : article de V. Mysore (Medium, 26/09/2026), dépôt `receptron/laya`,
synthèses sur Jev et Laya.

**Ce que c'est.** Un LLM (« Système 2 », pensée lente) **rédige** du texte, mot après mot. Un modèle
de décision (« Système 1 », pensée rapide, d'après Kahneman) ne rédige rien. On lui donne un **état**
(un texte ou un JSON) et des **questions typées** ; il renvoie, en un seul calcul, une **probabilité**
pour chaque réponse possible :

| Type de question | Exemple pour OptiFisc | Ce qui revient |
|---|---|---|
| `choice` (choix) | « Quel levier est le plus pertinent pour ce profil ? » parmi L01 à L05 | Une probabilité par option |
| `score` (échelle) | « Quel est le niveau de risque fiscal de cette proposition ? » de 1 à 4 | Une distribution et un score moyen |
| `noul` (oui/non) | « Cette proposition est-elle étayée par l'article cité ? » | P(vrai) |

Comme le modèle ne peut répondre **qu'avec les options fournies**, il n'y a ni texte à analyser ni
réponse hors sujet. Le code peut alors **brancher sur la probabilité** : au-dessus d'un seuil (ex.
0,90), affichage normal ; en dessous, signalement « à vérifier en priorité ».

| | **Jev** (TypeSafe AI) | **Laya** (Convai Innovations) |
|---|---|---|
| Nature | Propriétaire, API | Open source (Apache 2.0), 421 M de paramètres |
| Accès | Via **OpenRouter**, le fournisseur déjà retenu | Auto-hébergé (Python, Node.js, navigateur) ; environ 2 Go de mémoire |
| Coût | De l'ordre de 0,04 $ par million de jetons en entrée | Gratuit, sur notre propre matériel |
| Langue | À vérifier en français | Variante multilingue nécessaire pour le français |
| Limite principale | Les données sortent du cabinet | **Doit être spécialisé** (ré-entraîné) : sans cela, il fait à peine mieux que le hasard sur un benchmark de décisions typées, et il est trop sûr de lui |

**Ce qu'ils ne savent pas faire** (d'après leurs propres documentations) : calculer, et **inventer des
pistes**. Ils choisissent parmi des options qu'on leur donne. Ils ne remplacent donc pas l'agent
génératif, qui doit proposer des axes **hors catalogue**.

**Le rôle retenu : un duo Système 1 + Système 2** (même principe que la démo `layaAgent` de l'article) :

1. **Pré-tri** : avant l'agent, Jev évalue rapidement la pertinence de chaque levier du catalogue pour
   le profil pseudonymisé (`noul` par levier). L'agent commence par les leviers les plus probables.
2. **Juge des propositions** : après l'agent, Jev évalue chaque proposition (« étayée par l'article
   cité ? », « niveau de risque »). Sous le seuil, la proposition est marquée « confiance faible ».
3. Dans tous les cas, **l'humain décide** : la probabilité aide à prioriser la relecture, elle ne
   valide rien.

**Pourquoi Jev pour le MVP et Laya en perspective.**
- Jev passe par OpenRouter : même clé, même pare-feu de données, rien à installer sur le poste de la
  soutenance.
- Laya répondrait à la confidentialité (100 % local, même sur un processeur ordinaire). Mais il
  faudrait le **spécialiser sur des décisions fiscales étiquetées par le cabinet**, ce qui demande des
  données et du temps que nous n'avons pas d'ici le 31/10. C'est une très bonne perspective pour le
  mémoire : « remplacer Jev par Laya spécialisé, hébergé au cabinet ».
- Le port `ModeleDecision` rend ce remplacement possible sans toucher au métier.

#### Décision du 16/10/2026 : un « Système 1 » maison, sans Jev

Jev est payant, et le projet se limite aux solutions gratuites. On garde l'**idée** du Système 1
(questions fermées, réponse chiffrée, seuil, l'humain décide), mais le juge est **notre propre code
déterministe**, `JugeDeterministe`, qui implémente le port `ModeleDecision` :

| Question | Comment le juge y répond (sans IA) |
|---|---|
| **Pré-tri** : « ce levier est-il pertinent pour ce dossier ? » | Critères écrits dans `leviers.yaml` et évalués sur le profil : par exemple, réduire le résultat est inutile si le dossier est au minimum de perception ; le levier dons n'a d'intérêt que si la marge de plafond est positive. Le juge renvoie un score de 0 à 1 et la liste des critères remplis. |
| **Juge** : « cette proposition est-elle étayée ? » | Somme pondérée de contrôles vérifiables : l'article cité existe (obligatoire) ; il appartient au chapitre IS ; la justification et le texte de l'article partagent du vocabulaire (score BM25 normalisé) ; les conditions du levier sont remplies. Le juge renvoie un score de 0 à 1 et le détail de chaque contrôle. |

Avantages pour le mémoire : c'est **gratuit**, **instantané**, **hors ligne**, et surtout
**explicable** (« confiance 0,62 : article existant, chapitre IS, mais vocabulaire peu commun avec
l'article »). Un jury d'expertise comptable préfère un score justifié à une probabilité opaque. Le port
`ModeleDecision` permet de brancher Jev ou un Laya spécialisé plus tard, sans toucher au reste.

Pour le « Système 2 » (l'agent qui rédige), on utilise les **modèles gratuits d'OpenRouter**. Leurs
limites de débit et leur disponibilité changent souvent : le nom du modèle est un réglage, pas une
valeur écrite dans le code. À vérifier au jalon J11.

---

## Partie B — L'architecture

### B.1 Le problème que l'architecture résout

Dans la V2, le fichier `app.py` (1 207 lignes) mélangeait l'affichage, les calculs, la lecture de la
base et la gestion de l'état. Conséquences :

- impossible de tester le calcul de l'IS sans lancer l'interface ;
- une modification d'écran pouvait casser un calcul ;
- impossible d'expliquer simplement « où est la règle de l'art. 47 ».

### B.2 L'idée : le métier au centre, les outils autour

L'**architecture hexagonale** (ou « propre ») range le code en **quatre couches concentriques**. La règle
unique est la suivante : **une couche ne connaît que les couches plus intérieures qu'elle.**

```
        ┌────────────────────────────────────────────────────────────┐
        │  INTERFACE  (Streamlit : écrans, boutons, formulaires)      │
        │   ┌────────────────────────────────────────────────────┐   │
        │   │  INFRASTRUCTURE  (SQLite, Excel, Word, OpenRouter,   │   │
        │   │                   lecture YAML, lecture balance)     │   │
        │   │   ┌────────────────────────────────────────────┐   │   │
        │   │   │  APPLICATION  (cas d'usage : « calculer    │   │   │
        │   │   │   l'IS », « importer une balance »…)        │   │   │
        │   │   │   ┌────────────────────────────────────┐   │   │   │
        │   │   │   │  DOMAINE (métier pur : Balance,    │   │   │   │
        │   │   │   │  Dossier, Regle, ResultatFiscal,   │   │   │   │
        │   │   │   │  LigneAudit, Montant…)             │   │   │   │
        │   │   │   └────────────────────────────────────┘   │   │   │
        │   │   └────────────────────────────────────────────┘   │   │
        │   └────────────────────────────────────────────────────┘   │
        └────────────────────────────────────────────────────────────┘
              Les dépendances pointent toujours VERS LE CENTRE.
```

| Couche | Contient | A le droit d'importer | N'a PAS le droit d'importer |
|---|---|---|---|
| **Domaine** | Les objets du métier et leurs règles de cohérence (un montant de réintégration ne peut pas être négatif, une règle sans article est invalide…) | Uniquement la bibliothèque standard (`decimal`, `dataclasses`, `datetime`) | streamlit, sqlite3, pandas, openpyxl, yaml, requests |
| **Application** | Les cas d'usage : enchaînement des étapes d'une action métier. Les **ports** (interfaces des services dont elle a besoin). | Domaine | Toute bibliothèque technique |
| **Infrastructure** | Les **adaptateurs** : comment on lit un Excel, comment on écrit en SQLite, comment on appelle OpenRouter | Domaine, Application (pour implémenter ses ports), bibliothèques techniques | Interface |
| **Interface** | Les écrans Streamlit. Ils récupèrent les saisies, appellent un cas d'usage et affichent le résultat. | Application, Domaine (pour afficher les objets) | — (et **aucun calcul fiscal**) |

Un fichier spécial, `composition.py`, est le **seul** endroit qui assemble tout : il crée les
adaptateurs et les donne aux cas d'usage (injection de dépendances).

### B.3 Analogie pour s'en souvenir

Un cabinet d'expertise comptable :

- le **Domaine**, ce sont les **normes** (CGI, SYSCOHADA) : elles existent indépendamment de tout logiciel ;
- l'**Application**, ce sont les **procédures internes du cabinet** (« pour établir l'IS prévisionnel :
  1. récupérer la balance, 2. projeter, 3. retraiter, 4. calculer, 5. tracer ») ;
- l'**Infrastructure**, ce sont les **outils** (classeur Excel, armoire d'archives, messagerie) :
  on peut changer d'armoire sans changer la procédure ;
- l'**Interface**, c'est le **guichet** où le collaborateur dépose et reçoit les documents.

### B.4 Un exemple de bout en bout : « calculer l'IS prévisionnel »

```
[Écran Calcul]  clic « Calculer »
     │  envoie : identifiant du dossier
     ▼
[Application] CalculerIsPrevisionnel.executer(id_dossier)
     │ 1. depot_dossiers.charger(id)            ── port ──▶ [Infra] SQLite
     │ 2. referentiel.parametres(2026)          ── port ──▶ [Infra] YAML validé
     │ 3. projeter(balance, hypotheses)          (Domaine, pur)
     │ 4. appliquer_retraitements(...)           (Domaine, pur)
     │ 5. calculer_is(...)                       (Domaine, pur)
     │ 6. journal.enregistrer(lignes_audit)     ── port ──▶ [Infra] SQLite
     ▼
     renvoie : ResultatFiscal (objet immuable, montants Decimal, piste d'audit)
     │
[Écran Calcul]  affiche le résultat (formatage « 1 500 000 FCFA » fait ici, et seulement ici)
```

Ce que cet exemple montre :

- les étapes 3 à 5 sont **pures** : mêmes entrées, même sortie, aucun effet de bord. On peut les
  tester avec des chiffres calculés à la main, sans base ni écran ;
- l'écran ne calcule rien, il **demande** et **affiche** ;
- pour passer de SQLite à une autre base, on écrit un nouvel adaptateur. Rien d'autre ne change.

### B.5 Les ports prévus

| Port (défini dans l'Application) | Adaptateur(s) (dans l'Infrastructure) |
|---|---|
| `Referentiel` : paramètres, règles de retraitement, leviers d'un millésime | `ReferentielYaml` |
| `LecteurBalance` : fichier → `Balance` + rapport de lecture | `LecteurBalanceTableur` (Excel/CSV, repris de la V2) |
| `DepotDossiers`, `DepotUtilisateurs`, `DepotValidations` | `...Sqlite` |
| `Journal` : piste d'audit et historique | `JournalSqlite` |
| `RechercheArticles` : question → articles | `RechercheBm25` |
| `FournisseurIA` : question + articles → réponse citée ; boucle d'outils de l'agent | `OpenRouter`, `Ollama`, `IADesactivee` |
| `ModeleDecision` : état + questions typées → probabilités | `JevOpenRouter`, `DecisionDesactivee` (plus tard `LayaLocal`) |
| `GenerateurLivrables` : résultat → fichiers | `ExcelPilotage`, `NoteWord`, `LettreDgiWord` |
| `Horloge` : date du jour | `HorlogeSysteme` (et une horloge figée dans les tests des acomptes) |

L'horloge est un port pour une raison précise : le calcul des acomptes dépend de la date du jour. Pour
tester « le 15 mai, il reste 3 échéances », il faut pouvoir **fixer** la date dans le test.

### B.6 Arborescence cible

```
OF/
├── pyproject.toml          # description du projet et dépendances
├── README.md               # installation et lancement
├── .env.exemple            # modèle de configuration (clé OpenRouter vide)
├── .gitignore              # exclut .env, var/, .venv/
├── docs/                   # ce dossier de conception
├── referentiel/
│   ├── 2026/
│   │   ├── parametres.yaml       # taux, seuils, délais, plan comptable
│   │   ├── retraitements.yaml    # réintégrations et déductions
│   │   ├── leviers.yaml          # leviers d'optimisation
│   │   └── perimetre.yaml        # ce que l'outil couvre ou non
│   └── corpus/                   # CGI 2026 et LPF 2024 découpés par article (JSON)
├── src/optifisc/
│   ├── domaine/
│   ├── application/
│   ├── infrastructure/
│   ├── interface/streamlit/
│   └── composition.py
├── scripts/                # outils ponctuels (construire le corpus, générer les démos)
├── tests/
│   ├── domaine/  application/  infrastructure/  bout_en_bout/
│   └── donnees/            # balances de démonstration, cas chiffrés de référence
└── var/                    # NON versionné : base SQLite, livrables générés, journaux
```

Le détail de chaque sous-dossier sera écrit au fur et à mesure des jalons du plan (doc 06), et non
d'un bloc.

### B.7 Garde-fous automatiques

On ne compte pas seulement sur la discipline : des tests vérifieront l'architecture elle-même.

1. **Test d'architecture** : aucun fichier de `domaine/` ou d'`application/` n'importe `streamlit`,
   `sqlite3`, `openpyxl`, `yaml` ou `requests`.
2. **Test « pas de float »** : les objets du domaine refusent un `float` comme montant.
3. **Test du référentiel** : chaque règle YAML a un identifiant unique, un article et un statut, et
   chacune est utilisée par au moins un test chiffré.

---

## Décisions à valider

- [ OUI ] **D1.1** Python 3.12, Streamlit, SQLite, YAML + pydantic, pytest, ruff : stack retenue.
- [ OUI ] **D1.2** Conventions `Decimal` (A.2) : création depuis une chaîne, arrondi unique au franc en `ROUND_HALF_UP`, stockage en `TEXT`.
- [ OUI ] **D1.3** OpenRouter avec **pare-feu de données** (A.3) : aucune donnée client envoyée, assistant limité aux textes de loi, Ollama et « sans IA » disponibles en option.
- [ OUI ] **D1.4** Abandon de ChromaDB et de la recherche sémantique pour le MVP : BM25 seul. La recherche sémantique reste une perspective.
- [ OUI ] **D1.5** Architecture en 4 couches, règle de dépendance vers le centre, `composition.py` unique.
- [ OUI ] **D1.6** Les explications chiffrées propres au dossier sont générées par modèles de phrases (sans IA).
- [ OUI ] **D1.7** (nouveau, 14/10) Trois niveaux de données (public / pseudonymisé / identifiant) ; OpenRouter autorisé par défaut **uniquement pour les dossiers de démonstration** ; dossiers réels : activation explicite et tracée, ou fournisseur confidentiel.
- [ ✔ Révisé le 16/10 → juge déterministe maison + modèles gratuits OpenRouter (A.4). Commentaire d'origine : « JEV est payant a ce que je vois or moi je me focalise plus sur les model gratuit du coup SI IL Y EN A PAS ON LAISSE POUR LES MODEL DE CE GENRE a moin qu'on puis cree un logique cimilere sans forcement passez par jev » ] **D1.8** (nouveau) Ajout d'un modèle de décision « Système 1 » (Jev via OpenRouter) derrière le port `ModeleDecision`, pour le pré-tri et le jugement des propositions ; Laya local spécialisé en perspective.

## Historique des décisions

| Date | Décision | Motif |
|---|---|---|
| 2026-10-11 | Périmètre IS seul, Streamlit, dossier `OF/` | Validé après l'audit des V1 et V2 |
| 2026-10-14 | Section validée (D1.1 à D1.6) | — |
| 2026-10-14 | A.3 étendu : 3 niveaux de données, profil pseudonymisé pour l'agent, OpenRouter réservé par défaut aux dossiers de démonstration | Ajout de l'agent de propositions (UC14) ; lenteur de l'IA locale ; poste de soutenance sans Ollama |
