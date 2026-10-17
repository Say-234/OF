# Journal de bord

> À lire **en premier** au début de chaque session, par Salim ou par n'importe quel agent IA.
> À mettre à jour **à la fin** de chaque session. L'entrée la plus récente est en haut.

## État actuel

| | |
|---|---|
| **Phase** | Construction (l'agent construit, Salim supervise à la fin — décision du 16/10/2026) |
| **Jalon en cours** | Construction terminée (J0 à J12) : supervision et recette par Salim |
| **Prochaine action** | Salim : vérifier la conformité (doc 07, §5 écarts), tester avec une vraie clé OpenRouter, recette sur une balance réelle anonymisée, mise en ligne (doc 08) |
| **Tests** | 157 verts (`.venv/Scripts/python -m pytest -q`, ~1 min) ; ruff propre |
| **Lancer l'application** | `.venv/Scripts/python -m streamlit run src/optifisc/interface/streamlit/app.py` (mode cabinet) ; mode démo : variables `OPTIFISC_MODE=demo` et `OPTIFISC_MDP_DEMO=...` |
| **Retard sur le calendrier** | Aucun : J0 à J10 faits le 16/10 (en avance) |

## Questions ouvertes

- Premier appel réel à OpenRouter avec la clé de Salim : vérifier la tenue en français et le respect du protocole JSON par l'agent.
- Conditions de l'offre gratuite de Streamlit Community Cloud : dépôt privé, mise en veille (à vérifier à J12).
- Balance réelle anonymisée : à obtenir auprès du cabinet pour la recette (J12).

---

## Historique des sessions

### 17/10/2026 — Refonte visuelle verte, accueil et journal de missions
- **Demande de Salim** (maquette de référence) : pages trop plates ; une page d'accueil qui présente l'objectif, les rôles et l'année fiscale ; un tutoriel par rôle « comme dans un jeu vidéo », rejouable.
- **Design** : accent vert `#0E6B4E`, fond menthe, cartes blanches arrondies avec ombre (`style.css`, `composants.carte()`), menu actif en pastille verte (doc 05, A.3 révisé). Graphiques Altair avec le skill dataviz (`graphiques.py`) : synthèse (jauge + emphase de l'impôt appliqué), calcul (cascade), acomptes (normal / demandé). Indicateurs en tête du tableau de bord.
- **Accueil E00** (`app_pages/accueil.py`) avant la connexion, en démo et en cabinet → D4.4 révisée (doc 04, §8).
- **Journal de missions** : `application/tutoriel.py` (missions par rôle, étapes cochées par les données), table `preferences` (migration 002), `interface/streamlit/missions.py` (carte de la barre latérale « M'y emmener », fenêtre de première connexion, bandeau dans l'onglet concerné), page « Mes missions » (recommencer).
- **Typographie** choisie (Plus Jakarta Sans + Inter, doc 05, A.4 révisé) : fichiers de police à télécharger avec l'accord de Salim. **Logo** : à générer par Salim (prompt fourni), à déposer dans `interface/streamlit/static/`.
- **Tests** : tutoriel, préférences, accueil, missions des 3 rôles. Captures : `scripts/captures.py` (accueil → connexion → tutoriel → écrans).
- **À valider par Salim** : D4.9 (journal de missions), D5.10 (typographie, logo).
- **IA** : modèles gratuits de secours (`OPENROUTER_MODELES_SECOURS`, fournisseurs variés : Google sature par moments), une nouvelle tentative, réponses vides refusées.
- **Logo** fourni par Salim (originaux `docs/identite/`) : `scripts/preparer_logo.py` produit `static/logo.png` (barre latérale), `icone.png` (onglet, barre repliée), `logo_complet.png` (accueil, connexion), fond transparent et couleurs exactes de la charte.
- **En attente de Salim** : décision sur la « revue périodique par l'agent » (nouvelle balance au 30/09, 30/11, avant clôture → comparaison + agent relancé + note de revue).

### 16/10/2026 — Raccourcis de démonstration et guides
- Mode démo uniquement (refusés en cabinet, testé) : connexion en un clic par rôle (`Application.entrer_en_demo`), changement de rôle dans la barre latérale, « Tout mettre à néant » sur les retraitements (`ServiceDossiers.saisir_neant_restantes`, chaque saisie reste tracée), session de 4 h.
- Guides : `docs/09_guide_utilisateur.md` (qui fait quoi au cabinet, circuit d'un dossier, blocages fréquents) et `docs/10_scenario_soutenance.md` (déroulé minute par minute, parades).

### 16/10/2026 — Revue de design (skill ui-ux-pro-max)
- Style confirmé par le skill : « tableau de bord dense en données » (analyse financière). Corrections : marge haute réduite (thème `paddingTop`), bandeau démo déplacé en badge dans la barre latérale, points d'attention et liste de contrôle regroupés dans un seul cadre (`composants.liste_de_points`, icône colorée + texte), barre d'avancement dans le tableau de bord (`ProgressColumn`), compteurs sur tous les filtres, noms d'utilisateurs au lieu des e-mails (qui devenaient des liens), libellés d'actions accentués (`composants.action`), écran de connexion centré, en-tête de dossier aligné.

### 16/10/2026 — Modèles gratuits OpenRouter
- Consigne de Salim : **uniquement des modèles gratuits**. Appliquée dans le code : `infrastructure/openrouter.py` refuse tout modèle sans suffixe `:free`, avant tout appel (testé).
- Un modèle par usage : assistant `google/gemma-4-31b-it:free`, agent `nvidia/nemotron-3-super-120b-a12b:free` (identifiants vérifiés dans le catalogue public OpenRouter). Voir doc 08, §2.
- Aucun modèle de décision type Laya/Jev parmi les gratuits ; le juge déterministe reste en place. Perspective : le reranker gratuit de NVIDIA pourrait remplacer le contrôle « vocabulaire commun » du juge.
- `.env` créé localement (sans clé) ; Salim y colle sa clé.

### 16/10/2026 — Construction J11 et J12
- **J11** : `infrastructure/corpus.py`, `recherche_bm25.py` (10 questions étalons sur 10 dans les 5 premiers), `openrouter.py` (modèle gratuit en réglage), `ia_desactivee.py` ; `application/assistant.py` (pare-feu : montants et noms de clients bloqués) ; `application/agent/` : profil pseudonymisé, juge déterministe (seuil de confiance 0,70), boucle JSON sans framework (10 tours, 90 s), outils, service (article inexistant rejeté, nombres de l'IA masqués, gain recalculé par le moteur, dossier réel refusé par défaut). Testé avec une fausse IA scriptée.
- **Choix à connaître** : l'agent n'utilise pas l'« appel d'outils » natif (beaucoup de modèles gratuits ne le gèrent pas) mais un protocole JSON lisible, compatible avec tout modèle.
- **J12** : `lancer.bat`, `sauvegarder.bat` + `scripts/sauvegarder.py` (API de sauvegarde SQLite), `requirements.txt` (Streamlit Community Cloud), secrets de l'hébergeur lus comme variables d'environnement, `docs/08_mise_en_service.md`.
- **Non vérifié faute de clé** : un appel réel à OpenRouter (à faire par Salim, doc 08 §2).

### 16/10/2026 — Construction J6 à J10
- **J6** : `domaine/moteur/leviers.py` (L01 à L05, simulation avant/après), `acomptes.py` (échéancier, réduction, crédit d'impôt).
- **J7** : SQLite (`infrastructure/persistance/` : migrations numérotées, dépôts, journal en ajout seul protégé par des triggers), `securite.py` (PBKDF2, 8 caractères min.).
- **J8** : `application/autorisation.py` (matrice fail-closed, cloisonnement), `application/comptes.py` (blocage 5 échecs / 15 min).
- **J9-J10 application** : `application/` dossiers, balance (aperçu puis confirmation), calcul, scénarios, validation (empreinte par règle), livrables ; `infrastructure/livrables/` (Excel avec formules, note Word, lettre DGI) ; `composition.py` (+ mode démo : base recréée, comptes `*@demo.bj`, NOVA calculé). Parcours A et B testés de bout en bout (`tests/bout_en_bout/test_parcours.py`).
- **J9-J10 interface** : `interface/streamlit/` (app.py, app_pages/, ecrans/ par étape, composants, formats, etat), thème `.streamlit/config.toml` ; test de fumée AppTest (`tests/interface/`) ; captures `scripts/captures.py` → `var/captures/`.
- **Écarts de structure par rapport au doc 07** (à valider par Salim) : `app_pages/` au lieu de `pages/` (recommandation Streamlit) ; `ecrans/` (un module par étape du dossier) ; `application/dependances.py` ; `domaine/journal.py`, `domaine/scenario.py` ; `infrastructure/livrables/generateur.py`.

### 16/10/2026 — Construction J0 à J5
- **Décisions** : D1.8 / D3.8 tranchées (pas de Jev, payant) → « Système 1 » maison : `JugeDeterministe` (doc 01, A.4) ; IA générative = modèles gratuits d'OpenRouter. Méthode : l'agent construit, Salim supervise. Structure du code figée : `docs/07_structure_du_code.md`. Python 3.14 (installé).
- **J0** : git, `pyproject.toml`, `.venv`, `tests/test_architecture.py` (règle des 4 couches vérifiée automatiquement).
- **J1** : `domaine/montant.py` (Decimal, refus des float, arrondi au franc), `domaine/balance.py` (totaux par préfixe, contrôles).
- **J2** : `referentiel/2026/*.yaml` (repris de la V2, lus en Decimal exact), `domaine/referentiel.py`, `infrastructure/referentiel_yaml.py` (validation pydantic : une faute de frappe est refusée).
- **J3** : `infrastructure/lecteur_balance.py` (V2 sans pandas, en Decimal) ; balances de démo dans `referentiel/demo/`.
- **J4-J5** : `domaine/dossier.py` (cycle de vie), `domaine/moteur/projection.py`, `retraitements.py` (registre de stratégies), `impot.py`. **Jalon de vérité atteint** : BATI-PLUS et NOVA SERVICES donnent exactement les montants de la V2, au franc près (`tests/bout_en_bout/test_demos.py`).
- **Comment vérifier** : `.venv/Scripts/python -m pytest -q` ; lire `tests/domaine/test_moteur_impot.py` (cas chiffrés commentés) puis `domaine/moteur/impot.py`.

### 15/10/2026 — Préparation de la reprise multi-agents
- 10 paquets de skills installés globalement par Salim (`~/.agents/skills`, 129 skills).
- Création de `AGENTS.md` (consignes communes à tous les agents, choix des skills par moment, skills exclus), de `CLAUDE.md` (import de `AGENTS.md`) et de ce journal de bord.

### 14/10/2026 — Révision de la conception
- Validés : documents 01, 02, 04 (mot de passe : 8 caractères minimum).
- Ajouté : agent IA de propositions (UC14), profil pseudonymisé, OpenRouter réservé par défaut aux dossiers de démonstration.
- Ajouté : modèle de décision « Système 1 » (Jev via OpenRouter) pour le pré-tri et le jugement des propositions ; Laya local en perspective.
- Maquettes refaites avec le skill `ui-ux-pro-max` (diagnostic du style « vibe-codé » de la V2).
- Calendrier daté (dépôt au 31/10), plan de repli, démonstration en ligne + installation locale.

### 12/10/2026 — Dossier de conception initial
- Rédaction des documents 00 à 06 dans `OF/docs/`.

### 11/10/2026 — Audit des versions précédentes
- Audit de `opti_fisc` (V1 : bonne architecture) et `OptiFisc/OptiFisc_App` (V2 : bon contenu métier).
- Décisions : IS seul, Streamlit, nouveau projet propre dans `OF/`.
