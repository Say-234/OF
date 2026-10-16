# 07 — Structure du code (référence de conformité)

> **Objectif** : fixer, fichier par fichier, où vit chaque responsabilité. C'est la grille avec
> laquelle Salim vérifie, à la fin, que le code construit est conforme.
>
> **Méthode de travail révisée le 16/10/2026** : pour tenir le délai, l'agent IA **construit** et Salim
> **supervise**. Chaque jalon reste testé (test d'abord), commité séparément, et résumé dans le journal
> de bord : ce qui a été fait, comment le vérifier, quels fichiers lire.

## 1. Règle de dépendance (vérifiée par un test automatique)

```
interface ──▶ application ──▶ domaine ◀── infrastructure
                   ▲                            │
                   └──────── ports ◀────────────┘   (l'infrastructure implémente les ports)
composition.py : seul fichier qui importe tout et assemble.
```

- `domaine/` : bibliothèque standard uniquement (`decimal`, `dataclasses`, `datetime`, `enum`, `re`).
- `application/` : `domaine/` + bibliothèque standard.
- `infrastructure/` : peut importer `domaine/`, `application/ports.py` et les bibliothèques techniques.
- `interface/` : `application/`, `domaine/` (pour afficher), `streamlit`. **Jamais** `infrastructure/`.

Test : `tests/test_architecture.py` lit les imports de chaque fichier et échoue en cas de violation.

## 2. Arborescence

```
OF/
├── AGENTS.md                   consignes pour tout agent IA (CLAUDE.md l'importe)
├── README.md                   installation, lancement, tests
├── pyproject.toml              dépendances, configuration pytest et ruff
├── .env.exemple                modèle de configuration (clé OpenRouter, mode, modèle IA)
├── .gitignore                  .venv/, var/, .env, caches
├── .streamlit/config.toml      thème (jetons de couleur du doc 05)
├── lancer.bat                  lance l'application (Windows)
│
├── referentiel/                DONNÉES RÉGLEMENTAIRES, lisibles par un comptable
│   ├── 2026/
│   │   ├── parametres.yaml     taux, seuils, délais, plan comptable (repris de la V2)
│   │   ├── retraitements.yaml  catégories, 28 règles, sanctions hors résultat
│   │   ├── leviers.yaml        L01 à L06, conditions, paramètres, critères de pertinence
│   │   └── perimetre.yaml      couvert / non couvert / hypothèses
│   ├── corpus/                 cgi_2026.json, lpf_2024.json (articles découpés)
│   └── demo/                   dossiers de démonstration FICTIFS (balances + demos.yaml)
│
├── src/optifisc/
│   ├── domaine/                MÉTIER PUR : objets + calculs, aucun outil technique
│   │   ├── erreurs.py          exceptions métier (DonneeInvalide, BalanceIllisible, AccesRefuse, DossierFige…)
│   │   ├── montant.py          vers_decimal(), arrondir_fcfa() : seule porte d'entrée des montants
│   │   ├── balance.py          LigneBalance, Balance (totaux par préfixe de compte), contrôles
│   │   ├── referentiel.py      Parametres, PlanComptable, RegleRetraitement, Sanction, Levier, Referentiel
│   │   ├── dossier.py          Dossier, Secteur, CategorieTaux, Hypotheses, Ajustement, EtatDossier
│   │   ├── resultat.py         LigneAudit, Alerte, ResultatFiscal
│   │   ├── utilisateur.py      Role, Utilisateur
│   │   ├── proposition.py      Proposition, Decision, ProfilPseudonymise
│   │   └── moteur/             LE MOTEUR DE CALCUL (fonctions pures : mêmes entrées → même sortie)
│   │       ├── projection.py   projeter() : balance à date → balance au 31/12
│   │       ├── retraitements.py  une fonction par type de règle + registre (type → fonction)
│   │       ├── impot.py        calculer_is() : RC → RF → IS droit commun vs minimum → IS dû + ORTB
│   │       ├── leviers.py      effet de chaque levier (L01 à L05) + simuler()
│   │       └── acomptes.py     echeancier() et recommandation de réduction (art. 51-52)
│   │
│   ├── application/            CAS D'USAGE : orchestrent le domaine via les ports
│   │   ├── ports.py            interfaces : Referentiel, LecteurBalance, Depots, Journal, Horloge,
│   │   │                       RechercheArticles, FournisseurIA, ModeleDecision, GenerateurLivrables
│   │   ├── autorisation.py     matrice des droits (fail-closed) + exiger()
│   │   ├── dossiers.py         UC05 créer / lister / ouvrir ; UC06 hypothèses ; cycle de vie
│   │   ├── balance.py          UC01 aperçu puis confirmation de l'import
│   │   ├── calcul.py           UC02 retraitements, UC07 calcul de l'IS, UC08 acomptes
│   │   ├── scenarios.py        UC03 simuler / retenir un scénario
│   │   ├── validation.py       UC04 soumettre / valider / renvoyer / rouvrir ; UC10 valider une règle
│   │   ├── livrables.py        UC04 générer les livrables
│   │   ├── comptes.py          UC12 connexion ; UC13 utilisateurs et attributions
│   │   ├── assistant.py        UC09 question → articles → réponse IA (pare-feu)
│   │   └── agent/              UC14
│   │       ├── profil.py       construire_profil_pseudonymise()
│   │       ├── outils.py       outils offerts à l'agent (lire_profil, rechercher_articles, simuler_levier…)
│   │       ├── boucle.py       boucle « le modèle choisit un outil → on l'exécute », tours limités
│   │       └── juge.py         JugeDeterministe : pré-tri des leviers, score des propositions
│   │
│   ├── infrastructure/         ADAPTATEURS : implémentent les ports avec des outils techniques
│   │   ├── referentiel_yaml.py lecture + validation (pydantic) des YAML → objets du domaine
│   │   ├── lecteur_balance.py  Excel/CSV → Balance + rapport de lecture (repris de la V2)
│   │   ├── persistance/
│   │   │   ├── connexion.py    ouverture SQLite, application des migrations
│   │   │   ├── migrations/001_initial.sql
│   │   │   └── depots.py       dossiers, utilisateurs, validations, journal (ajout seul)
│   │   ├── securite.py         hachage PBKDF2, vérification, politique de mot de passe
│   │   ├── horloge.py          HorlogeSysteme
│   │   ├── corpus.py           chargement des articles JSON
│   │   ├── recherche_bm25.py   RechercheArticles locale
│   │   ├── openrouter.py       FournisseurIA (modèles gratuits), appels HTTP
│   │   ├── ia_desactivee.py    FournisseurIA qui ne fait rien (mode sans IA)
│   │   └── livrables/
│   │       ├── excel.py        dossier de calcul (totaux en formules)
│   │       └── word.py         note de pilotage + lettre au DGI
│   │
│   ├── interface/streamlit/    ÉCRANS : aucune logique métier
│   │   ├── app.py              point d'entrée, navigation, garde d'authentification
│   │   ├── etat.py             accès typé à st.session_state (identifiants seulement)
│   │   ├── composants.py       entete, badge, onglets d'étapes, champ_montant, tableau…
│   │   ├── formats.py          affichage des montants, dates, pourcentages (seul lieu de formatage)
│   │   └── pages/              un fichier par écran (E01 à E17)
│   │
│   └── composition.py          assemblage : crée les adaptateurs et les cas d'usage
│
├── scripts/                    outils ponctuels (créer un compte, réinitialiser la démo)
└── tests/
    ├── test_architecture.py    règle de dépendance
    ├── domaine/                montants, balance, moteur (cas chiffrés à la main)
    ├── application/            cas d'usage avec de faux adaptateurs
    ├── infrastructure/         YAML, lecteur de balance, SQLite, sécurité, BM25
    └── bout_en_bout/           balances de démo → résultat attendu (jalon de vérité J5)
```

`var/` (non versionné) contient la base SQLite, les livrables générés et les journaux techniques.

## 3. Choix de structure à connaître

| Choix | Raison |
|---|---|
| Le **moteur** est dans `domaine/moteur/` | Ce sont des calculs purs sur des objets métier : ils n'ont besoin d'aucun outil. Les tester ne demande ni base, ni écran (doc 01, B.4). |
| Un **fichier par concept**, pas un dossier par type de règle | Les 5 types de retraitement font chacun 5 à 15 lignes : un seul fichier `retraitements.py` avec un registre est plus lisible que 5 fichiers minuscules. |
| `referentiel.py` du domaine ≠ `referentiel_yaml.py` de l'infrastructure | Le domaine décrit **ce qu'est** une règle ; l'infrastructure sait **la lire** dans un fichier. Changer de format (JSON, base) ne touche pas le domaine. |
| Le juge de l'agent est dans `application/agent/` | C'est notre propre logique déterministe (doc 01, A.4), pas un service externe. |
| Les montants sont arrondis **à chaque ligne de la piste d'audit** et les totaux sont des sommes de lignes arrondies | Le tableau de passage tombe juste au franc, comme un comptable l'attend. |

## 4. Correspondance jalons → fichiers

| Jalon | Fichiers créés |
|---|---|
| J0 | `pyproject.toml`, `.gitignore`, `.env.exemple`, `README.md`, `tests/test_architecture.py` |
| J1 | `domaine/erreurs.py`, `montant.py`, `balance.py` |
| J2 | `referentiel/2026/*.yaml`, `domaine/referentiel.py`, `application/ports.py`, `infrastructure/referentiel_yaml.py` |
| J3 | `infrastructure/lecteur_balance.py`, `referentiel/demo/` |
| J4 | `domaine/dossier.py`, `domaine/moteur/projection.py`, `domaine/moteur/retraitements.py` |
| J5 | `domaine/resultat.py`, `domaine/moteur/impot.py`, `tests/bout_en_bout/` |
| J6 | `domaine/moteur/leviers.py`, `domaine/moteur/acomptes.py` |
| J7 | `infrastructure/persistance/`, `infrastructure/horloge.py` |
| J8 | `domaine/utilisateur.py`, `application/autorisation.py`, `application/comptes.py`, `infrastructure/securite.py` |
| J9-J10 | `application/` (autres cas d'usage), `interface/streamlit/`, `infrastructure/livrables/`, `composition.py` |
| J11 | `infrastructure/corpus.py`, `recherche_bm25.py`, `openrouter.py`, `ia_desactivee.py`, `application/assistant.py`, `application/agent/` |
| J12 | `lancer.bat`, `scripts/`, mise en ligne |

## 5. Écarts constatés pendant la construction (16/10/2026) — à valider par Salim

| Prévu (§2) | Construit | Raison |
|---|---|---|
| `interface/streamlit/pages/` | `interface/streamlit/app_pages/` | Recommandation de Streamlit 1.66 : `pages/` déclenche l'ancienne découverte automatique des pages. |
| Un fichier par écran dans `pages/` | `app_pages/` (écrans de navigation) + `ecrans/` (un module par étape du dossier, E05 à E13, et le panneau de l'agent) | Les étapes du dossier partagent l'en-tête et les onglets : une seule page `dossier.py` les aiguille. |
| `interface/streamlit/composants.py`, `formats.py`, `etat.py` | Identiques | — |
| — | `application/dependances.py` | Regroupe les ports donnés aux cas d'usage (rempli par `composition.py`). |
| — | `domaine/journal.py` (événement d'audit), `domaine/scenario.py` | Objets du domaine apparus avec la persistance et UC03. |
| `domaine/proposition.py` | + `Article`, `ArticleTrouve`, `ReponseAssistant` | Les objets de l'assistant et de l'agent sont regroupés. |
| `application/agent/` (profil, outils, boucle, juge) | + `service.py` | Le service applique les garde-fous et enregistre les décisions. |
| `infrastructure/livrables/` (excel, word) | + `generateur.py` | Implémente le port `GenerateurLivrables` (choisit les fichiers à produire). |
| `application/comptes.py` : attribution des dossiers | Déplacée dans `application/dossiers.py` | Une seule méthode d'attribution, à côté des autres cas d'usage des dossiers. |
| — | `lancer.bat`, `sauvegarder.bat`, `requirements.txt`, `scripts/captures.py`, `scripts/sauvegarder.py`, `docs/08_mise_en_service.md` | Jalon J12 (mise en service). |
| — | `tests/interface/` | Test de fumée de chaque écran (AppTest, sans navigateur). |

La règle de dépendance (§1) est inchangée et vérifiée par `tests/test_architecture.py`.
