# AGENTS.md — Consignes pour tout agent IA travaillant sur OptiFisc

Ce fichier est la **source unique des consignes** pour n'importe quel agent de code (Claude Code,
Codex, Gemini CLI, Cursor, OpenCode, Copilot…). `CLAUDE.md` ne fait que l'importer. Si tu es un
agent qui reprend le projet, **lis ce fichier en entier avant toute action**.

## 1. Le projet en bref

- **OptiFisc** : outil d'aide au pilotage de l'**impôt sur les sociétés (IS)** en cours d'exercice
  pour les cabinets d'expertise comptable au **Bénin** (CGI 2026, SYSCOHADA révisé).
- Prototype du **mémoire DECOFI** de Salim. **Dépôt au plus tard le 31/10/2026.**
- Salim **débute en Python**. Son objectif absolu : **comprendre chaque décision et chaque ligne**.
  Ce n'est pas du « vibe coding ».
- Langue : **français** pour les échanges, les docs, l'interface, les noms du domaine métier.

## 2. Protocole de début et de fin de session (obligatoire)

**Au début de chaque session :**
1. Lire [`docs/JOURNAL_DE_BORD.md`](docs/JOURNAL_DE_BORD.md) : jalon en cours, dernière action, prochaine action, questions ouvertes.
2. Lire [`docs/README.md`](docs/README.md) : état de validation des documents de conception.
3. Lire le document de conception lié au jalon en cours (voir `docs/06_plan_mvp.md`, §3).
4. Lancer `python -m pytest -q` (dès que le code existe) et annoncer le résultat **avant** de modifier quoi que ce soit.
5. Résumer à Salim, en 3 à 5 lignes, où on en est et ce qu'on propose de faire.

**À la fin de chaque session (même interrompue) :**
1. Mettre à jour `docs/JOURNAL_DE_BORD.md` : fait, en cours, prochaine action précise, questions ouvertes, décisions prises.
2. Si une décision de conception a changé, l'inscrire dans la rubrique « Historique des décisions » du document concerné.
3. Commit git avec un message clair (voir §6).

Le journal de bord est ce qui permet à **un autre agent** de reprendre sans rien perdre. Il doit
toujours être à jour.

## 3. Documents de référence (la conception est figée avant le code)

| Document | Contenu |
|---|---|
| `docs/00_glossaire.md` | Vocabulaire métier et technique |
| `docs/01_stack_et_architecture.md` | Stack, `Decimal`, confidentialité IA, 4 couches, ports |
| `docs/02_acteurs_et_permissions.md` | Rôles, cycle de vie du dossier, matrice des droits |
| `docs/03_cas_utilisation.md` | UC01 à UC14 |
| `docs/04_parcours_utilisateur.md` | Écrans E01 à E18 et enchaînements |
| `docs/05_interfaces_et_flux.md` | Design system, maquettes, flux de données |
| `docs/06_plan_mvp.md` | Jalons J0 à J12, calendrier, plan de repli, déploiement |

**Ne jamais contredire un document validé sans le dire à Salim et obtenir son accord.**

## 4. Règles non négociables

1. **L'IA ne calcule jamais un impôt.** Tout montant sort du moteur déterministe et a sa ligne de piste d'audit (règle, article, base, formule). L'IA propose, le moteur chiffre, l'humain décide.
2. **Montants en `Decimal`**, créés depuis une chaîne ou un entier ; arrondi unique au franc (`ROUND_HALF_UP`) via `arrondir_fcfa()` ; jamais de `float` après la lecture du fichier ; stockage SQLite en `TEXT`.
3. **Architecture en 4 couches** : `domaine` ← `application` ← `infrastructure` / `interface`. Le domaine et l'application n'importent ni `streamlit`, ni `sqlite3`, ni `openpyxl`, ni `yaml`, ni `requests`.
4. **Aucun taux, seuil, délai ou compte en dur dans le Python** : tout est dans `referentiel/2026/*.yaml`, avec son article.
5. **Droits « fail-closed »**, vérifiés dans les cas d'usage (jamais seulement en masquant un bouton).
6. **Pare-feu de données** : aucune donnée identifiante (raison sociale, IFU, libellés de comptes, balance détaillée) n'est envoyée à un service d'IA. L'agent ne reçoit que le profil pseudonymisé. OpenRouter n'est autorisé par défaut que pour les dossiers de démonstration.
7. **Secrets** : la clé API est dans `.env` (non versionné), jamais dans le code ni dans un commit.

## 5. Méthode de travail : la boucle pédagogique (doc 06, §1)

Pour **chaque** morceau de code :

1. **Expliquer** ce qu'on va écrire et pourquoi (concept Python + règle métier), avant d'écrire.
2. **Tester d'abord** : écrire le test avec des chiffres calculés à la main ; le voir échouer.
3. **Écrire** le plus petit code qui fait passer le test (10 à 40 lignes en général).
4. **Faire relire** à Salim, ligne par ligne ; répondre à toutes ses questions.
5. **Salim lance lui-même** `python -m pytest`.
6. **Salim reformule** ce que fait le code. S'il n'y arrive pas, on reprend à l'étape 1 en plus simple.
7. **Commit**.

Contraintes :
- **Un seul fichier de code nouveau par boucle.** Jamais l'application entière d'un bloc.
- **Pas de code non compris** : « je ne comprends pas cette ligne » suffit pour la réécrire plus simplement.
- Préférer du code **simple et explicite** à du code astucieux (pas de compréhensions imbriquées, pas de métaprogrammation).
- Commenter le **pourquoi** (règle métier, article du CGI), pas le quoi.
- Un jour de retard sur le calendrier déclenche le **plan de repli** (doc 06, §2.2), jamais une réduction des explications.

## 6. Conventions de code

- Python 3.12, `pyproject.toml`, environnement virtuel `.venv`, tests `pytest`, style `ruff`.
- Noms du domaine en **français** sans accents dans les identifiants (`resultat_fiscal`, `arrondir_fcfa`) ; accents autorisés dans les chaînes et les commentaires.
- Type hints partout ; `@dataclass(frozen=True)` pour les objets du domaine.
- Erreurs métier = exceptions typées du domaine (`BalanceIllisible`, `AccesRefuse`…).
- Commits en français, au présent, préfixés par le jalon : `J1: ajoute arrondir_fcfa et ses tests`.

## 7. Skills à utiliser

Les skills sont installés globalement dans `~/.agents/skills/<nom>/SKILL.md`. Si ton agent ne les
charge pas automatiquement, **lis le fichier `SKILL.md` correspondant** au moment indiqué. Si un skill
est absent, applique le résumé de la colonne de droite.

| Moment | Skill(s) | Si le skill est absent, retenir |
|---|---|---|
| Début de session | `context-engineering` | Charger seulement le contexte utile : journal, doc du jalon, fichiers touchés |
| Démarrer un jalon | `writing-plans`, `planning-and-task-breakdown` | Découper le jalon en tâches de 15 à 30 min, chacune avec son test |
| Chaque tâche de code | `test-driven-development`, `python-testing-patterns`, `incremental-implementation` | Rouge → vert → refactor ; une tranche fine et vérifiable à la fois |
| Garder le code minimal | `lean-build`, `ponytail-review` (en revue seulement) | Pas de fonctionnalité non demandée ; réutiliser avant d'écrire |
| Expliquer du code à Salim | `understand-explain` | Explication pas à pas d'un fichier ou d'une fonction, avec un exemple |
| Bug, test rouge inattendu | `systematic-debugging`, `investigate-first` | Reproduire, isoler la cause, prouver par un test, puis corriger |
| Avant de dire « c'est fini » | `verification-before-completion` | Lancer réellement les tests et montrer la sortie |
| Fin de jalon | `code-review-and-quality`, `code-simplification` | Revue : justesse, lisibilité, respect des 4 couches |
| Sécurité (J8, J11, J12) | `security-and-hardening`, `security-review` | Entrées, authentification, secrets, données envoyées à l'IA |
| Git | `git-workflow-and-versioning` | Petits commits cohérents, messages clairs |
| Décision d'architecture | `documentation-and-adrs` | Noter la décision, le motif et les alternatives dans « Historique des décisions » |
| Schémas pour le mémoire | `archify` | Diagrammes d'architecture, de séquence, d'états |
| API externes (OpenRouter, Jev, Streamlit) | `source-driven-development` | Vérifier dans la documentation officielle avant d'implémenter |
| Interface Streamlit (J9, J10) | `developing-with-streamlit` (prioritaire), `ui-ux-pro-max`, `impeccable`, `accessibility` | Respecter `docs/05_interfaces_et_flux.md` : natif d'abord, une action principale, tableaux |
| Tests de l'interface, captures | `webapp-testing` | Playwright sur les parcours A et B |
| Mise en ligne (J12) | `shipping-and-launch` | Liste de contrôle avant mise en ligne ; données fictives seulement |
| Cartographier le code existant | `understand`, `graphify` | Graphe des modules et dépendances (utile pour le mémoire et la reprise) |
| Préparer la reprise par un autre agent | `understand-onboard` | Guide de prise en main généré à partir du code |

**Skills à NE PAS activer sur ce projet** :
- `caveman`, `ultracave`, `megacave`, `cavecrew` : réponses ultra-compressées, incompatibles avec la pédagogie.
- `ponytail` en **mode permanent** : il réduit les explications. Utiliser seulement `ponytail-review` pour une revue ponctuelle.
- `dispatching-parallel-agents`, `subagent-driven-development`, `using-git-worktrees` : le travail est séquentiel et pédagogique ; pas de sous-agents sauf demande explicite de Salim.
- Les skills de marketing, de design graphique ou de réseaux sociaux : hors sujet.

## 8. Commandes utiles (à compléter au jalon J0)

```bash
# activer l'environnement (Windows, Git Bash)
source .venv/Scripts/activate
# tests
python -m pytest -q
# style
ruff check .
# lancer l'application (à partir de J9)
streamlit run src/optifisc/interface/streamlit/app.py
```
