# 02 — Acteurs du système, rôles et permissions

> **Objectif de ce document** : savoir qui utilise l'outil, ce que chacun a le droit de faire, et
> comment l'outil empêche ce qui n'est pas permis.

---

## 1. Les acteurs

Un **acteur** est quelqu'un (ou quelque chose) qui interagit avec le système. On distingue les acteurs
**principaux**, qui se connectent, et les acteurs **secondaires**, qui reçoivent un résultat ou
fournissent un service sans se connecter.

### 1.1 Acteurs principaux (ils ont un compte)

| Acteur | Qui c'est dans le cabinet | Ce qu'il attend de l'outil | Niveau de confiance |
|---|---|---|---|
| **Collaborateur** (junior ou confirmé) | Prépare les dossiers clients au quotidien | Gagner du temps sur la préparation, ne rien oublier dans les retraitements, savoir quel article s'applique | Prépare, mais **ne valide rien** |
| **Expert-comptable** | Signe et engage sa responsabilité professionnelle | Contrôler rapidement le travail préparé, valider les règles et les notes, en garder la preuve | **Valide** les règles et les livrables |
| **Administrateur** | Personne chargée de l'outil (souvent l'expert lui-même ou un associé dans un petit cabinet) | Créer les comptes, attribuer les dossiers, sauvegarder | Gère les accès, **pas le contenu fiscal** |

### 1.2 Acteurs secondaires (pas de compte)

| Acteur | Rôle vis-à-vis du système |
|---|---|
| **Client du cabinet** (la société) | Fournit la balance et les informations complémentaires ; reçoit la note de pilotage. Il n'accède jamais à l'outil. |
| **Administration fiscale (DGI)** | Destinataire de la lettre de demande de réduction des acomptes (art. 52). |
| **Fournisseur d'IA** (OpenRouter) | Service externe qui rédige des réponses à partir des articles du CGI. Il ne reçoit aucune donnée client (doc 01, A.3). |
| **Logiciel comptable du client** | Source du fichier de balance (export Excel ou CSV). Pas de connexion directe. |

---

## 2. Les objets à protéger

Avant les droits, il faut savoir **ce qu'on protège** :

| Objet | Pourquoi il est sensible |
|---|---|
| **Dossier client** (balance, saisies, résultats) | Secret professionnel ; données financières confidentielles |
| **Référentiel de règles** (validation des règles) | Une règle fausse fausse tous les dossiers |
| **Livrables validés** | Engagent la signature de l'expert-comptable |
| **Comptes utilisateurs** | Donnent accès à tout le reste |
| **Piste d'audit** | Preuve de qui a fait quoi : elle ne doit jamais être modifiable |

---

## 3. Le cycle de vie d'un dossier

Les droits dépendent aussi de l'**état** du dossier. Un dossier validé, par exemple, ne doit plus
pouvoir être modifié en silence.

```
  ┌───────────┐  import balance   ┌────────────────┐  calcul lancé   ┌──────────┐
  │ BROUILLON │ ────────────────▶ │ EN PRÉPARATION │ ──────────────▶ │ CALCULÉ  │
  └───────────┘                   └────────────────┘ ◀────────────── └──────────┘
                                          ▲          toute modification    │
                                          │          des données           │ soumettre
                                          │                                ▼
                                          │  renvoyer avec          ┌──────────────┐
                                          └──────────────────────── │ À VALIDER    │
                                             commentaire (expert)   └──────────────┘
                                                                           │ valider (expert)
                                                                           ▼
                              rouvrir (expert, motif obligatoire)   ┌──────────────┐
                        EN PRÉPARATION ◀────────────────────────── │   VALIDÉ     │
                                                                    └──────────────┘
                                                                           │ livrables générés
                                                                           ▼
                                                                    ┌──────────────┐
                                                                    │   LIVRÉ      │
                                                                    └──────────────┘
```

Règles de cohérence :

1. Toute modification de données (balance, saisie, hypothèse) sur un dossier `CALCULÉ` le ramène à
   `EN PRÉPARATION`, car le résultat affiché n'est plus à jour.
2. En `À VALIDER`, le collaborateur ne peut plus modifier le dossier. Il attend la décision de l'expert.
3. En `VALIDÉ` et `LIVRÉ`, le dossier est **figé**. Le résultat validé est enregistré tel quel (montants,
   version du référentiel, date, valideur). Pour corriger, l'expert doit **rouvrir** avec un motif, et
   la réouverture est tracée.
4. Chaque changement d'état est inscrit dans la piste d'audit.

---

## 4. Matrice des permissions

Légende : ✅ autorisé · ❌ refusé · 🔸 autorisé sous condition (voir la note).

| Action | Collaborateur | Expert-comptable | Administrateur |
|---|---|---|---|
| Se connecter, changer son mot de passe | ✅ | ✅ | ✅ |
| Voir la liste des dossiers | 🔸 ses dossiers | ✅ tous | ✅ tous (en-têtes seulement) |
| Créer un dossier client | ✅ | ✅ | ❌ |
| Importer une balance, saisir, lancer les calculs | 🔸 ses dossiers, état ≤ CALCULÉ | ✅ état ≤ CALCULÉ | ❌ |
| Simuler des leviers, enregistrer une décision de levier | 🔸 ses dossiers | ✅ | ❌ |
| Interroger l'assistant CGI | ✅ | ✅ | ✅ |
| Soumettre un dossier à validation | 🔸 ses dossiers | ✅ | ❌ |
| Valider ou renvoyer un dossier | ❌ | ✅ | ❌ |
| Rouvrir un dossier validé | ❌ | ✅ (motif obligatoire) | ❌ |
| Générer les livrables **provisoires** (filigrane « projet ») | 🔸 ses dossiers | ✅ | ❌ |
| Générer les livrables **définitifs** | ❌ | 🔸 dossier VALIDÉ | ❌ |
| Consulter le référentiel de règles | ✅ | ✅ | ✅ |
| Valider une règle du référentiel (sur un cas chiffré) | ❌ | ✅ | ❌ |
| Modifier les fichiers YAML du référentiel | ❌ (hors application) | ❌ (hors application) | ❌ (hors application) |
| Consulter la piste d'audit d'un dossier | 🔸 ses dossiers | ✅ | ✅ |
| Créer, désactiver un compte, changer un rôle | ❌ | ❌ | ✅ |
| Attribuer un dossier à un collaborateur | ❌ | ✅ | ✅ |
| Sauvegarder / restaurer la base | ❌ | ❌ | ✅ |

**« Ses dossiers »** : les dossiers dont le collaborateur est désigné responsable. C'est le
**cloisonnement** : un collaborateur ne voit pas les clients des autres.

**Pourquoi l'administrateur ne touche pas au fiscal.** C'est le principe de **séparation des tâches** :
celui qui gère les accès ne doit pas pouvoir aussi modifier un résultat. Dans un petit cabinet, une
même personne peut avoir deux comptes (expert et admin). Elle doit alors se connecter avec le bon
compte pour chaque usage, et la trace reste claire.

**Pourquoi le YAML n'est pas modifiable dans l'application.** Une règle fiscale change avec la loi de
finances, une fois par an. On modifie alors le fichier, on relance les tests chiffrés, puis l'expert
re-valide la règle dans l'application. Permettre l'édition en ligne ouvrirait une porte à des
modifications non testées.

---

## 5. Comment l'outil fait respecter ces règles

### 5.1 Principe « fail-closed »

La V2 autorisait par défaut une action non listée. On inverse ce principe :

- chaque action protégée a un **nom** (ex. `valider_dossier`) ;
- la matrice ci-dessus est écrite **une seule fois**, dans le code de la couche Application
  (`application/autorisation.py`), et non dans un YAML modifiable ;
- **une action absente de la matrice est refusée.**

### 5.2 Le contrôle est fait par le cas d'usage, pas par l'écran

Masquer un bouton n'est pas une protection. Chaque cas d'usage reçoit l'utilisateur courant et
**vérifie lui-même** le droit avant d'agir. L'écran masque en plus les boutons interdits, pour le
confort, mais la vraie barrière est côté Application. Ainsi, même un écran mal programmé ne peut pas
contourner la règle.

```
Écran ──▶ ValiderDossier.executer(utilisateur, id_dossier)
              │
              ├─ autorisation.exiger(utilisateur, "valider_dossier", dossier)  ── refus ⇒ erreur « Accès refusé »
              ├─ vérifier l'état == À VALIDER                                   ── sinon ⇒ erreur métier
              └─ figer le résultat, changer l'état, tracer
```

### 5.3 Mesures de sécurité des comptes

| Mesure | Détail |
|---|---|
| Stockage des mots de passe | Empreinte **PBKDF2-SHA256** salée, avec un grand nombre d'itérations (repris de la V2). Jamais le mot de passe en clair. |
| Comparaison | En temps constant (`hmac.compare_digest`), contre les attaques par mesure de temps. |
| Robustesse | 8 caractères minimum à la création ou au changement (décision D2.7 du 14/10/2026), et refus des mots de passe les plus courants (`motdepasse`, `12345678`, nom du cabinet…). |
| Premier mot de passe | Généré aléatoirement par l'administrateur et à changer à la première connexion. **Aucun mot de passe écrit dans un fichier de configuration.** |
| Tentatives | Après 5 échecs, compte bloqué 15 minutes ; l'événement est tracé. |
| Session | Déconnexion automatique après 30 minutes d'inactivité. |
| Désactivation | Un compte est **désactivé**, jamais supprimé, pour que la piste d'audit reste lisible. |
| Mode démonstration | Comptes de démo créés **uniquement** si l'application est lancée explicitement en mode démo, avec une base séparée. |

### 5.4 Piste d'audit inviolable (en pratique)

- La table du journal n'accepte que des **ajouts** : le code n'offre aucune fonction de modification
  ni de suppression.
- Chaque entrée contient : date et heure (format ISO), utilisateur, rôle, dossier, action, détail, et
  la version du référentiel utilisée.
- Limite à assumer dans le mémoire : un fichier SQLite reste modifiable par quelqu'un qui a accès au
  disque. La protection repose sur les droits d'accès Windows au dossier `var/` et sur les sauvegardes.

---

## Décisions à valider

- [ OUI ] **D2.1** Trois rôles (Collaborateur, Expert-comptable, Administrateur), avec séparation admin / fiscal.
- [ OUI ] **D2.2** Cloisonnement : un collaborateur ne voit que les dossiers qui lui sont attribués.
- [ OUI ] **D2.3** Cycle de vie à 6 états, avec dossier figé une fois validé et réouverture motivée.
- [ OUI ] **D2.4** Livrables provisoires (filigrane) pour le collaborateur, définitifs pour l'expert seulement.
- [ OUI ] **D2.5** Matrice des droits dans le code (fail-closed), contrôlée par les cas d'usage.
- [ OUI ] **D2.6** Un expert peut-il valider un dossier **qu'il a lui-même préparé** ? Proposition : **oui**, car c'est la réalité d'un petit cabinet, mais c'est signalé dans la piste d'audit (« préparé et validé par la même personne »).
- [ OUI (saufe pour le nombre de caracter requis pour le mot de  passe 8 caractère minimume pas 12) ] **D2.7** Mesures de sécurité des comptes du §5.3. 
