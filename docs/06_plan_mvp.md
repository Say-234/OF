# 06 — Plan de construction et de mise en service du MVP

> **Objectif de ce document** : fixer l'**ordre** dans lequel on construit, ce qu'on apprend à chaque
> étape, et comment on sait qu'une étape est terminée. On construit **de l'intérieur vers
> l'extérieur** : le métier d'abord, l'écran en dernier.

---

## 1. Méthode de travail à chaque séance (anti « vibe coding »)

Chaque morceau de code suit la même boucle courte :

```
 1. EXPLIQUER   Claude explique ce qu'on va écrire et pourquoi (concept Python + règle métier).
 2. TESTER      On écrit D'ABORD le test, avec des chiffres calculés à la main.
                Il échoue (normal : le code n'existe pas encore).
 3. ÉCRIRE      Claude écrit le plus petit code qui fait passer le test (souvent 10 à 40 lignes).
 4. LIRE        Tu relis ligne par ligne ; tu poses toutes tes questions.
 5. LANCER      Tu lances toi-même `python -m pytest` ; le test passe.
 6. REFORMULER  Tu expliques avec tes mots ce que fait le code. Si tu n'y arrives pas, on reprend en 1.
 7. ENREGISTRER Commit git avec un message qui dit ce qui a été fait.
```

Règles :

- **Jamais plus d'un fichier de code nouveau par boucle.**
- **Aucun code sans test**, sauf l'interface Streamlit, qui se vérifie à l'œil sur les balances de démo.
- **Aucune ligne non comprise ne reste.** « Je ne comprends pas cette ligne » est une raison
  suffisante pour la réécrire plus simplement.
- Chaque jalon se termine par une **mini-revue** : ce que tu as appris, ce qui reste flou.

Le test d'abord (étape 2) a un intérêt particulier pour un mémoire d'expertise comptable : le test,
c'est **le cas chiffré qu'un expert vérifierait à la main**. Il sert donc à la fois de preuve technique
et de pièce justificative.

---

## 2. Vue d'ensemble des jalons

```
 J0  Poste de travail ─┐
 J1  Domaine : montants et balance ─┐
 J2  Référentiel YAML ──────────────┤  MÉTIER PUR (sans écran, sans base)
 J3  Lecteur de balance ────────────┤  → testable entièrement par pytest
 J4  Projection et retraitements ───┤
 J5  Calcul de l'IS ────────────────┘  ★ Jalon de vérité : résultats V2 retrouvés au franc près
 J6  Leviers et acomptes ───────────── fin du moteur
 J7  Persistance et journal ────────┐
 J8  Comptes et droits ─────────────┘  INFRASTRUCTURE
 J9  Interface : préparer et analyser ┐
 J10 Interface : décider et livrer ───┘  INTERFACE
 J11 Assistant CGI + agent de propositions   IA (en dernier : le reste ne dépend pas d'elle)
 J12 Recette, mise en ligne de la démo, installation au cabinet
```

### 2.1 Calendrier (révisé le 14/10/2026)

Contraintes : **dépôt au plus tard le 31/10/2026** ; objectif de finir le développement vers le
27/10 pour garder une marge de recette. Cela fait **environ un jalon par jour**. C'est un rythme
soutenu pour une méthode où tu dois comprendre chaque ligne : le plan de repli (§2.2) existe pour
protéger cette compréhension plutôt que la quantité de fonctionnalités.

| Jalon | Date cible | Contenu | Point de contrôle |
|---|---|---|---|
| J0 | mer. 14/10 | Poste de travail | `1 passed` |
| J1 | jeu. 15/10 | Domaine : montants et balance | |
| J2 | ven. 16/10 | Référentiel YAML | |
| J3 | sam. 17/10 | Lecteur de balance | |
| J4 | dim. 18/10 | Projection et retraitements | |
| J5 | lun. 19/10 | Calcul de l'IS | ★ démos V2 retrouvées au franc près |
| J6 | mar. 20/10 | Leviers et acomptes | **Moteur complet** (ta date de marge initiale) |
| J7 | mer. 21/10 | Persistance et journal | |
| J8 | jeu. 22/10 | Comptes et droits | |
| J9 | ven. 23/10 | Interface : préparer et analyser | Parcours A jusqu'au calcul |
| J10 | sam. 24/10 → dim. 25/10 | Interface : décider et livrer | Parcours A et B complets |
| J11 | lun. 26/10 → mar. 27/10 | Assistant CGI + agent de propositions | |
| J12 | mer. 28/10 → jeu. 29/10 | Recette, mise en ligne, installation | Démo en ligne accessible |
| — | ven. 30/10 | Marge (imprévus, captures pour le mémoire) | |
| — | **sam. 31/10** | **Dépôt** | |

Règle de pilotage : chaque soir, on compare l'avancement au calendrier. **Un jour de retard déclenche
le plan de repli**, au lieu de compresser la phase d'explication.

### 2.2 Plan de repli (ce qu'on retire, dans cet ordre, si le retard s'installe)

| Ordre | Retiré ou simplifié | Ce qui le remplace |
|---|---|---|
| 0 | Jev (pré-tri et juge des propositions) | Agent seul ; Jev passe en perspective avec Laya |
| 1 | Écran Utilisateurs (UC13) | Comptes créés par un script en ligne de commande |
| 2 | Écran Journal (E16) | Les 3 derniers événements sur la synthèse + export Excel |
| 3 | Lettre au DGI (Word) | Paragraphe dans la note de pilotage |
| 4 | Plusieurs scénarios par dossier | Un seul scénario |
| 5 | Validation des règles à l'écran (UC10) | Statut « validée » renseigné dans le YAML par l'expert |
| 6 | Formats de balance à 6 et 8 colonnes | Formats 4 colonnes et solde signé seulement |
| 7 | Agent de propositions (UC14) | Assistant CGI seul ; l'agent passe en perspective, avec sa conception (doc 03) |

Ce qu'on **ne retire jamais** : J1 à J6 (le moteur et ses tests), les droits (J8), le parcours A.

Pourquoi l'IA est en dernier : l'outil doit être **complet et juste sans elle**. Si OpenRouter est
indisponible le jour de la soutenance, la démonstration du calcul fonctionne quand même.

---

## 3. Détail des jalons

### J0 — Poste de travail

| | |
|---|---|
| **Objectif** | Un environnement propre et reproductible dans `OF/`. |
| **Tu apprends** | Ce qu'est un environnement virtuel, `pyproject.toml`, git (commit, historique), lancer pytest. |
| **Livrables** | `git init` ; `.gitignore` ; `pyproject.toml` minimal ; `.venv` ; arborescence vide (doc 01, B.6) ; un premier test trivial qui passe ; `README.md` d'installation. |
| **Terminé quand** | `python -m pytest` affiche `1 passed` sur ta machine, et tu sais expliquer chaque ligne de `pyproject.toml`. |

### J1 — Domaine : montants et balance

| | |
|---|---|
| **Objectif** | Les briques de base du métier, sans aucune dépendance. |
| **Tu apprends** | `dataclass(frozen=True)`, `Decimal`, type hints, lever une exception, `@property`. |
| **Livrables** | `domaine/montant.py` (`arrondir_fcfa`, refus des `float`) ; `domaine/balance.py` (`LigneBalance`, `Balance` avec `total_charges(prefixes)` et `total_produits(prefixes)`) ; `domaine/erreurs.py`. |
| **Tests** | Arrondi (0,5 → au-dessus) ; refus d'un `float` ; un préfixe `647` qui couvre `6471` ; produits comptés en positif. |
| **Terminé quand** | Les tests passent, plus le **test d'architecture** (aucun import interdit dans `domaine/`). |

### J2 — Référentiel YAML

| | |
|---|---|
| **Objectif** | Charger les paramètres 2026, les 28 règles et les leviers, et **refuser un fichier mal formé**. |
| **Tu apprends** | Lire du YAML, pydantic (modèles, validation), notion de port (`Referentiel`) et d'adaptateur (`ReferentielYaml`). |
| **Livrables** | `referentiel/2026/*.yaml` (format fusionné V1 + V2, repris et relu règle par règle) ; `domaine/regle.py` ; `application/ports.py` (premier port) ; `infrastructure/referentiel/`. |
| **Tests** | Chaque règle a un id unique, un article, un statut ; un taux est un `Decimal` ; un YAML avec une faute de frappe dans un `type` est refusé avec un message clair. |
| **Terminé quand** | Tu peux ajouter une règle fictive au YAML et voir le test la refuser, puis l'accepter une fois corrigée. |

### J3 — Lecteur de balance

| | |
|---|---|
| **Objectif** | Lire les vraies balances Excel ou CSV en `Balance` + `RapportLecture`. |
| **Tu apprends** | openpyxl et csv, expressions régulières (simples), conversion aux frontières (`float` → `Decimal`), gestion des encodages. |
| **Livrables** | `infrastructure/balance/` : portage **progressif** du lecteur de la V2 (d'abord 4 colonnes, puis solde signé, puis 6 à 8 colonnes, puis en-tête sur 2 lignes) ; `domaine` : contrôles d'équilibre. |
| **Tests** | Les fichiers de `tests/donnees/` (balances de démo et formats variés de la V2) ; montant français `1 234 567,89` ; ligne de total ignorée ; compte de regroupement ignoré. |
| **Terminé quand** | Les 2 balances de démo et les 2 formats variés sont lus, avec un rapport exact. |

### J4 — Projection et retraitements

| | |
|---|---|
| **Objectif** | Projeter au 31/12, puis appliquer les règles de retraitement. |
| **Tu apprends** | Le patron « stratégie » : un dictionnaire `type → fonction`, à la place d'une longue chaîne de `if/elif`. Les fonctions pures. |
| **Livrables** | `application/projeter_balance.py` ; `application/retraitements/` (une fonction par type : `totalite`, `plafond_ca`, `plafond_ebe`, `saisie`, `plafond_saisie`) ; `LigneRetraitement`. |
| **Tests** | Un test chiffré **par type de règle**, commenté avec le calcul fait à la main. |
| **Terminé quand** | Les 28 règles s'appliquent sur une balance de démo, et tu sais expliquer comment ajouter un 6e type. |

### J5 — Calcul de l'IS ★ jalon de vérité

| | |
|---|---|
| **Objectif** | Résultat fiscal, IS de droit commun, minimum de perception, IS dû, ORTB, seuil de bascule, piste d'audit. |
| **Tu apprends** | Composer des fonctions, construire une piste d'audit, les tests « bout en bout ». |
| **Livrables** | `application/calculer_is.py` ; `domaine/resultat.py` (`ResultatFiscal`, `LigneAudit`, alertes sous forme de **codes**). |
| **Tests** | Cas chiffrés : minimum de perception supérieur à l'IS ; résultat déficitaire ; imputation des déficits (art. 43) ; taux de 25 %. **Les deux balances de démo doivent redonner, au franc près, les résultats attendus par les tests de la V2.** |
| **Terminé quand** | Ces deux tests passent. C'est la preuve que la nouvelle architecture n'a rien perdu du métier. |

### J6 — Leviers et acomptes

| | |
|---|---|
| **Objectif** | Simulation des leviers L01 à L05, échéancier et réduction des acomptes. |
| **Tu apprends** | Les dates en Python (`datetime.date`), le port `Horloge` (une date figée pour les tests). |
| **Livrables** | `application/leviers/` (un module par levier) ; `application/acomptes.py`. |
| **Tests** | Coefficient dégressif selon la durée ; gain nul au minimum de perception ; demande de réduction possible le 15 mai, mais trop tard le 5 décembre. |
| **Terminé quand** | **Le moteur est complet.** Tout le métier tourne sans écran ni base. |

### J7 — Persistance et journal

| | |
|---|---|
| **Objectif** | Enregistrer dossiers, balances, saisies, scénarios et journal dans SQLite. |
| **Tu apprends** | SQL de base (CREATE, INSERT, SELECT), requêtes paramétrées (`?`, contre l'injection SQL), migrations numérotées, transactions. |
| **Livrables** | `infrastructure/persistance/` (connexion, `migrations/001_initial.sql`, dépôts) ; montants en `TEXT` ; dates ISO ; journal en ajout seul. |
| **Tests** | Sur une **base temporaire** : enregistrer puis relire un dossier, et retrouver exactement les mêmes `Decimal` ; le journal ne propose aucune modification. |
| **Terminé quand** | Un dossier complet survit à un redémarrage. |

### J8 — Comptes et droits

| | |
|---|---|
| **Objectif** | Authentification, matrice des droits (fail-closed), cycle de vie du dossier. |
| **Tu apprends** | Hachage de mot de passe, principe du moindre privilège, machine à états. |
| **Livrables** | `infrastructure/securite/` ; `application/autorisation.py` ; `EtatDossier` et ses transitions. |
| **Tests** | Un collaborateur ne peut ni valider ni voir le dossier d'un autre ; une action inconnue est refusée ; un dossier `VALIDÉ` refuse une modification ; blocage après 5 échecs. |
| **Terminé quand** | Toute la matrice du doc 02 est couverte par des tests. |

### J9 — Interface : préparer et analyser

| | |
|---|---|
| **Objectif** | Écrans E01 à E09 branchés sur les cas d'usage. |
| **Tu apprends** | Streamlit (widgets, pages, `session_state`), `composition.py` (assembler l'application). |
| **Livrables** | `interface/streamlit/` : `app.py`, composants du design system, pages Connexion, Tableau de bord, Création, Vue dossier, Balance, Hypothèses, Retraitements, Calcul. |
| **Vérification** | Parcours A (doc 04) déroulé à la main sur BATI-PLUS, jusqu'au calcul. |
| **Terminé quand** | Aucun calcul dans `interface/` (relecture), et le parcours fonctionne de bout en bout. |

### J10 — Interface : décider et livrer

| | |
|---|---|
| **Objectif** | Écrans E10 à E13, E15 à E18 ; génération des livrables. |
| **Tu apprends** | openpyxl en écriture (formules Excel), python-docx. |
| **Livrables** | Pages Leviers, Acomptes, Soumission/Validation, Livrables, Référentiel, Journal, Utilisateurs ; `infrastructure/livrables/`. |
| **Tests** | Le fichier Excel contient les bons totaux (relus par le test) ; la note Word contient l'IS et les réserves ; filigrane « PROJET » présent sur une version provisoire. |
| **Terminé quand** | Parcours A puis B (doc 04) déroulés sur les deux dossiers de démo. |

### J11 — Assistant CGI et agent de propositions

| | |
|---|---|
| **Objectif** | (1) Recherche BM25 + réponse par OpenRouter. (2) Agent à outils qui produit des propositions (UC14). |
| **Tu apprends** | Appel d'une API HTTP, `.env`, délais d'attente et erreurs réseau ; puis le principe d'un agent : une **boucle** « le modèle choisit un outil → notre code l'exécute → on renvoie le résultat », avec une limite de tours. On l'écrit à la main (50 à 80 lignes), sans framework. |
| **Livrables** | `infrastructure/ia/` (BM25, `OpenRouter`, `IADesactivee`) ; `application/repondre_question.py` ; `application/agent/` (boucle, outils, `construire_profil_pseudonymise`) ; page E14 et panneau de l'agent sur E10. |
| **Tests** | Les 14 questions étalons de la V1 trouvent le bon article dans les 5 premiers résultats. IA **simulée** dans les tests : une fausse IA qui appelle des outils selon un script écrit d'avance. Le profil pseudonymisé ne contient ni raison sociale, ni IFU, ni libellé. Un article inventé est rejeté. Un nombre écrit par l'IA n'est jamais affiché comme montant. L'agent refuse un dossier réel avec un fournisseur non confidentiel. Sans réseau, tout le reste fonctionne. |
| **Terminé quand** | Sur BATI-PLUS, l'agent produit au moins une proposition chiffrée par le moteur et une piste à étudier, chacune avec un article réel. |
| **Si le temps le permet** | Adaptateur `JevOpenRouter` du port `ModeleDecision` : pré-tri des leviers et jugement des propositions, avec un test qui simule les probabilités (une probabilité de 0,85 doit afficher « confiance faible »). |

### J12 — Recette et mise en service au cabinet

| | |
|---|---|
| **Objectif** | Vérifier l'ensemble avec un regard d'utilisateur, mettre en ligne l'instance de démonstration (§4.5), puis installer sur le poste du cabinet. |
| **Recette** | Dérouler les parcours A, B et C sur les deux dossiers de démo + **une vraie balance anonymisée** fournie par le cabinet ; noter chaque anomalie ; corriger ; rejouer tous les tests. |
| **Validation métier** | L'expert-comptable valide dans l'outil les règles utilisées par les dossiers de démo (UC10). |
| **Livrables** | Guide d'installation, guide utilisateur court (une page par parcours), captures d'écran pour le mémoire. |

---

## 4. Mise en service au cabinet (déploiement local)

### 4.1 Configuration cible

| Élément | Choix |
|---|---|
| Poste | Un PC Windows du cabinet |
| Accès | Navigateur du même poste, `http://localhost:8501` |
| Données | Dossier `var/` (base SQLite, livrables), avec des droits Windows restreints aux comptes du cabinet |
| IA | Clé OpenRouter dans `.env` ; IA désactivable dans le fichier de configuration |

### 4.2 Procédure d'installation (à détailler en J0 et J12)

1. Installer Python 3.12 (case « Add to PATH » cochée).
2. Copier le dossier de l'application.
3. Créer l'environnement virtuel et installer les dépendances (une commande).
4. Copier `.env.exemple` en `.env`, puis y coller la clé OpenRouter.
5. Lancer `initialiser.bat` : crée la base et le premier compte administrateur (mot de passe affiché une seule fois).
6. Lancer `lancer.bat` : ouvre l'application dans le navigateur.

### 4.3 Exploitation

| Sujet | Procédure |
|---|---|
| **Sauvegarde** | Copie quotidienne de `var/` vers un support externe ou un dossier sauvegardé (script `sauvegarder.bat`, à planifier dans Windows). Restauration testée au moins une fois avant la mise en service. |
| **Mise à jour du référentiel** | Nouvelle loi de finances → nouveau dossier `referentiel/2027/` → tests chiffrés → validation des règles par l'expert. Les dossiers 2026 restent calculés avec le référentiel 2026. |
| **Mise à jour de l'application** | Sauvegarde, remplacement du code, migrations automatiques au démarrage, tests de fumée. |
| **Incident** | Journal technique dans `var/journaux/` ; aucune donnée client dans les messages d'erreur. |

### 4.4 Plusieurs postes (hors MVP)

Ouvrir l'application aux autres postes du réseau local est techniquement simple (Streamlit écoute sur
le réseau). Mais sans HTTPS, les mots de passe circuleraient en clair sur le réseau du cabinet.
**Proposition pour le MVP : un seul poste.** Le multi-postes sécurisé (HTTPS, reverse proxy) va dans
les perspectives.

### 4.5 Instance de démonstration en ligne (décision D6.4 du 14/10/2026)

**Besoin** : le poste de la soutenance n'est pas le tien et n'aura rien d'installé. Il faut donc une
démonstration accessible **depuis un simple navigateur**.

**Principe : deux installations du même code, qui diffèrent par leur configuration.**

| | Instance **en ligne** (démonstration) | Instance **locale** (cabinet) |
|---|---|---|
| Public | Toi, ton directeur de mémoire, le jury | Collaborateurs et expert du cabinet |
| Données | **Uniquement** les dossiers fictifs (BATI-PLUS, NOVA SERVICES) | Dossiers réels |
| Mode | `MODE=demo` : bandeau permanent « Démonstration — n'importez aucune donnée réelle », base recréée à chaque démarrage | `MODE=cabinet` |
| IA | OpenRouter (dossiers de démonstration : autorisé par défaut, doc 01 A.3) | Selon le choix du cabinet |
| Accès | HTTPS fourni par l'hébergeur ; comptes de démonstration (mots de passe communiqués au jury) | `localhost`, poste unique |

**Hébergeur proposé : Streamlit Community Cloud.** C'est gratuit, l'application se déploie depuis un
dépôt GitHub, le HTTPS est fourni et la clé OpenRouter se range dans les « secrets » de la plateforme.
Points à vérifier au jalon J12 (les conditions de l'offre gratuite peuvent avoir changé) :

- un dépôt **privé** est-il accepté ? Sinon, le code sera public, ce qui est sans risque puisqu'aucune donnée réelle ni clé n'est dans le dépôt ;
- l'application se met en **veille** après une période d'inactivité : il faudra l'ouvrir quelques minutes avant la présentation ;
- le disque est **temporaire** : c'est voulu, la base de démonstration est recréée à chaque démarrage.

**Plan B le jour de la soutenance** (si internet tombe) : instance locale sur ton PC ou une clé USB,
avec l'IA désactivée, plus une **courte vidéo** du parcours complet, agent compris, enregistrée à J12.

---

## 5. Ce qui n'est PAS dans le MVP (perspectives du mémoire)

- Autres impôts (TVA, IBA, TPS, ITS, patente), régimes particuliers, exercices décalés.
- Recherche sémantique (embeddings), interface vocale.
- Multi-postes en réseau, connexion directe aux logiciels comptables, dépôt e-services DGI.
- Chiffrement de la base.
- Saisonnalité de la projection (au-delà du coefficient d'activité).

---

## Décisions à valider

- [ OUI ] **D6.1** La boucle de travail en 7 temps (§1), avec le test écrit avant le code.
- [ OUI ] **D6.2** L'ordre des jalons J0 à J12 : le métier d'abord, l'IA en dernier.
- [ OUI ] **D6.3** J5 comme « jalon de vérité » : retrouver au franc près les résultats des démos de la V2.
- [ ✔ Révisé le 14/10 → §4.5 (commentaire d'origine : « ACCES EN LIGEN POUR LE MEMORANT ») ] **D6.4** Déploiement MVP sur **un seul poste**, sans accès réseau.
- [ ✔ Révisé le 14/10 → §2.1 : marge visée le 20/10, dépôt au plus tard le 31/10 ] **D6.5** As-tu une **date de soutenance** ou une échéance de dépôt ? Elle permettra de dater chaque jalon et de décider ce qui bascule en perspective si le temps manque.
- [ OUI ] **D6.6** Peux-tu obtenir du cabinet **une vraie balance anonymisée** pour la recette (J12) ?
- [ OUI ] **D6.7** (nouveau) Calendrier §2.1 : un jalon par jour, fin du développement le 27/10, recette les 28 et 29/10, dépôt le 31/10.
- [ OUI ] **D6.8** (nouveau) Plan de repli §2.2 et son ordre (l'agent est le dernier retiré).
- [ OUI ] **D6.9** (nouveau) Deux instances : démonstration en ligne (Streamlit Community Cloud, données fictives seulement) et locale au cabinet, avec un plan B (local + vidéo).
