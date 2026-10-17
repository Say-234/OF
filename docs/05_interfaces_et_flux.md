# 05 — Interfaces (UI/UX) et circulation des données

> **Objectif de ce document** : fixer à quoi ressemblent les écrans principaux et **comment les données
> circulent** entre l'écran et le métier. Les maquettes sont structurelles : elles montrent
> l'organisation et le contenu, pas le rendu exact.
>
> Les montants qui apparaissent dans les maquettes sont **fictifs et illustratifs**.
>
> **Révision du 14/10/2026 (D5.2)** : la disposition des écrans de la V2 faisait trop « design
> vibe-codé ». Les parties A et B ont été refaites avec le skill `ui-ux-pro-max` (style minimaliste
> suisse, palette « B2B Service », règles d'accessibilité WCAG). La partie C (flux de données) est inchangée.

---

## Partie A — Le design system

### A.1 Diagnostic : pourquoi la V2 faisait « vibe-codé »

Constats faits sur les captures de la V2 (`OptiFisc_App/sorties/captures/`) :

| Symptôme dans la V2 | Pourquoi c'est un problème | Correction retenue |
|---|---|---|
| La position est indiquée **4 fois** : fil d'Ariane, barre à chevrons, surtitre « ÉTAPE 4 SUR 6 », liste d'étapes dans la barre latérale | Bruit visuel ; l'œil ne sait pas où regarder | **Un seul** repère par niveau : barre latérale = navigation générale ; onglets d'étapes = navigation dans le dossier |
| 4 à 5 lignes d'explication avant le contenu (surtitre, titre, paragraphe, pastille « À FAIRE », 2e paragraphe) | Le contenu utile commence à mi-écran ; ton « tutoriel » | Titre + **une** ligne. L'aide détaillée va dans les infobulles des champs (`help=`) et dans un « Aide » repliable |
| Tout est dans une **carte** (chaque levier, chaque section, l'« étape suivante ») | Effet « maquette générée » ; pas de hiérarchie | Des **tableaux** pour les listes, des **séparateurs** pour les sections, des cartes seulement pour les indicateurs clés |
| Contenu dans une colonne étroite au centre, colonne d'historique presque vide à droite | Espace perdu ; les tableaux de montants sont à l'étroit | Pleine largeur ; panneau latéral **uniquement** quand il sert (comparaison, propositions de l'agent) |
| Montants saisis bruts (`52000000`) avec boutons +/− et « = 52,0 M FCFA » en dessous | Peu lisible, risque d'erreur de zéro | Champ texte aligné à droite, séparateur de milliers, suffixe « FCFA », pas de boutons +/− |
| Grands chiffres en gras sur les cartes de dossiers | Style « tableau de bord marketing » | Liste en **tableau triable**, montants en taille normale |
| Bouton principal désactivé à côté d'un bouton secondaire au même niveau | On ne sait pas quelle est l'action attendue | **Une seule action principale** par écran, en bas à droite de la section concernée |
| Étiquettes flottantes (« À confirmer », « À étudier ») accrochées à la barre latérale | Éléments qui semblent mal placés | Statut affiché **dans** l'onglet d'étape (texte + icône) |
| Phrase « L'IA ne calcule pas l'impôt » répétée sur chaque écran | Effet slogan | Dite une fois, dans le pied de page de l'application |

### A.2 Principes retenus

| Principe | Règle concrète |
|---|---|
| **Style** | Minimalisme suisse : grille, alignements stricts, typographie, beaucoup de blanc utile, aucun effet décoratif |
| **Natif d'abord** | On utilise les composants Streamlit natifs (`st.dataframe`, `st.tabs`, `st.metric`, `st.expander`, `st.dialog`, `st.toast`). Le HTML sur mesure est réservé à 2 composants (badge de statut, barre d'étapes). Moins de HTML = rendu plus cohérent et moins de risques de sécurité |
| **Une action principale par écran** | Un seul bouton plein (bleu) ; les autres actions sont des boutons secondaires (contour) ou des liens |
| **La couleur porte un statut, et jamais seule** | Chaque statut a une **couleur + une icône + un texte** (accessibilité : daltonisme, projection) |
| **Bleu = action uniquement** | Liens et boutons ; jamais pour décorer un titre |
| **Montants** | Chiffres tabulaires, alignés à droite, séparateur de milliers en espace (`36 800 000`), unité dans l'en-tête de colonne (« Montant (FCFA) ») plutôt que répétée sur chaque ligne |
| **Mode clair uniquement** | Lisible au vidéoprojecteur et à l'impression ; le mode sombre n'apporte rien à ce métier |
| **Densité** | Standard-compacte : un tableau de 28 règles doit tenir sur un écran sans défilement excessif |
| **Accessibilité** | Contraste du texte ≥ 4,5:1 ; focus clavier visible ; libellé visible sur chaque champ ; message d'erreur sous le champ concerné |
| **Hors ligne** | Police par défaut de Streamlit (embarquée), aucune ressource chargée depuis internet |
| **Échappement** | Tout texte venant d'une saisie ou d'un fichier est échappé par les composants, jamais par l'écran |

### A.3 Jetons (tokens) de couleur

> **Révision du 17/10/2026 — accent vert** (maquette de référence fournie par Salim : fond menthe, cartes
> blanches arrondies). Valeurs en vigueur, définies dans `.streamlit/config.toml` et `interface/streamlit/style.css` :
>
> | Jeton | Valeur | Usage |
> |---|---|---|
> | `action` | `#0E6B4E` (vert profond) | Boutons principaux, liens, onglet et menu actifs (blanc sur vert : 6,5:1) |
> | `fond` | `#EEF4F1` (menthe très pâle) | Fond de l'application : les cartes blanches s'en détachent |
> | `surface` | `#FFFFFF` + ombre légère, rayon 14 px | Cartes (`composants.carte()`), tableaux, graphiques |
> | `bordure` | `#DCE7E1` | Contours des cartes et des champs |
> | `texte` / `texte_secondaire` | `#10231C` / `#4A5E56` | Texte principal / aides (6,2:1 sur le fond) |
> | `accent_clair` | `#DCEFE6` | Bandeau « mission en cours » du tutoriel |
> | graphiques | `#0B7A55` / `#4CC38A` / gris `#B9C6C0` | Paire validée par le script du skill dataviz (ΔE daltonisme 22) |
>
> Les couleurs de statut (succès, attention, risque, info) sont inchangées, toujours avec icône et texte.
> Le tableau qui suit est la palette d'origine (bleue), conservée pour l'historique de la conception.

Palette « B2B Service » proposée par le skill, complétée par les couleurs de statut. Elle est définie
**une seule fois** (`interface/streamlit/composants/jetons.py`) et reprise dans `.streamlit/config.toml`.

| Jeton | Valeur | Usage |
|---|---|---|
| `texte` | `#0F172A` (marine très foncé) | Titres et texte principal |
| `texte_secondaire` | `#475569` | Libellés, aides, métadonnées |
| `fond` | `#F8FAFC` | Fond de l'application |
| `surface` | `#FFFFFF` | Tableaux, panneaux |
| `bordure` | `#E2E8F0` | Séparateurs, contours |
| `action` | `#0369A1` (bleu) | Boutons principaux, liens, focus |
| `succes` | `#15803D` + icône ✓ | Fait, conforme, validé |
| `attention` | `#B45309` + icône ▲ | À faire, à vérifier, à valider |
| `risque` | `#B91C1C` + icône ✕ | Erreur, risque, refus |
| `info` | `#475569` + icône ⓘ | Information neutre |

> Les icônes ci-dessus sont des repères pour la maquette. Dans l'application, ce seront les icônes
> Material de Streamlit (`:material/check_circle:` …), jamais des emojis.

### A.4 Typographie et espacement

> **Révision du 17/10/2026 — typographie.** Titres : **Plus Jakarta Sans** (600-700), géométrique et
> chaleureuse, proche de la maquette. Texte, tableaux et montants : **Inter** (400-600), très lisible en petite
> taille, **chiffres tabulaires** (colonnes de montants alignées). Deux polices libres (licence SIL OFL),
> **hébergées dans l'application** (`interface/streamlit/static/`) : aucun appel à Google Fonts, l'application
> reste utilisable hors ligne au cabinet. Tant que les fichiers ne sont pas déposés, la police de Streamlit
> s'applique (lignes `font` / `headingFont` commentées dans `config.toml`). Icônes : **Material Symbols**
> (`:material/…:`), la bibliothèque intégrée à Streamlit ; jamais d'emoji. Logo : fichier professionnel
> `static/logo.svg` (+ `static/icone.svg`), affiché automatiquement par `composants.preparer_page()`.
> La liste ci-dessous est la version d'origine.

- Police : celle de Streamlit (Source Sans), chiffres tabulaires pour les montants.
- Échelle de tailles : 12 (métadonnées) · 14 (tableaux, aides) · 16 (texte) · 20 (titre de section) · 24 (titre d'écran).
- Graisses : 600 pour les titres, 400 pour le texte, 500 pour les libellés de colonnes.
- Espacement sur une grille de 8 px : 8 entre éléments liés, 16 entre champs, 32 entre sections.

### A.5 Gabarit commun de tous les écrans

```
┌──────────────┬──────────────────────────────────────────────────────────────────────────────────┐
│ OptiFisc     │  Titre de l'écran                                          [Action principale]   │
│              │  Une ligne qui dit à quoi sert l'écran.                                          │
│ Dossiers     │  ────────────────────────────────────────────────────────────────────────────────│
│ Assistant CGI│                                                                                  │
│ Référentiel  │  CONTENU (pleine largeur, ou 8/12 + panneau 4/12 si utile)                       │
│ Journal      │                                                                                  │
│              │                                                                                  │
│ ──────────── │                                                                                  │
│ Salim A.     │                                                                                  │
│ Collaborateur│  ────────────────────────────────────────────────────────────────────────────────│
│ Déconnexion  │  OptiFisc · CGI Bénin 2026 · Les montants sont calculés par le moteur de règles  │
└──────────────┴──────────────────────────────────────────────────────────────────────────────────┘
```

Dans un dossier, un **en-tête de dossier** s'ajoute sous le titre :

```
  BATI-PLUS SARL · IS 2026 · BTP · balance au 30/06/2026          ▲ À valider    Resp. Salim A.
  ┌─────────┬────────────┬────────────────┬──────────┬──────────┬──────────┬──────────┬────────┐
  │ Synthèse│ 1 Balance ✓│ 2 Hypothèses ✓ │ 3 Retrait.│ 4 Calcul │ 5 Leviers│ 6 Acompt.│ 7 Livrer│
  └─────────┴────────────┴────────────────┴──────────┴──────────┴──────────┴──────────┴────────┘
```

Le statut de chaque étape (✓ fait, ▲ à faire, rien = pas encore commencé) est dans l'onglet lui-même.
La barre latérale ne répète **pas** les étapes.

### A.6 Composants (catalogue)

| Composant | Base Streamlit | Usage |
|---|---|---|
| `entete_ecran(titre, sous_titre, action)` | `st.title` + `st.caption` + `st.button` | Gabarit commun |
| `entete_dossier(vue)` | HTML minimal | Ligne d'identité du dossier + badge d'état |
| `onglets_etapes(etats, courante)` | HTML minimal / `st.segmented_control` | Navigation dans le dossier |
| `badge(statut)` | HTML minimal (échappé) | Couleur + icône + texte |
| `tableau_montants(df, colonnes_montant)` | `st.dataframe` + `column_config` | Tri, alignement à droite, format des milliers |
| `champ_montant(libelle, aide)` | `st.text_input` + conversion `Decimal` | Saisie d'un montant (un seul composant, testé) |
| `indicateurs([...])` | `st.metric` | 3 indicateurs au maximum par rangée |
| `detail_audit(ligne)` | `st.expander` | Règle, article, base, formule |
| `confirmation(question)` | `st.dialog` | Actions irréversibles (valider, rouvrir, remplacer la balance) |
| `vide(texte, action)` | `st.info` | État vide avec l'action à faire |

---

## Partie B — Maquettes des écrans principaux

### E03 — Tableau de bord (liste des dossiers)

```
 Dossiers                                                                  [+ Nouveau dossier]
 Dossiers IS de l'exercice 2026.
 ─────────────────────────────────────────────────────────────────────────────────────────────────
 [ Tous 7 ] [ À valider 1 ] [ En préparation 2 ] [ Livrés 4 ]          Rechercher [___________]

 Client ▲            Secteur    Arrêté      IS prévisionnel (FCFA)  Régime         État             Prochaine échéance
 ─────────────────────────────────────────────────────────────────────────────────────────────────
 BATI-PLUS SARL      BTP        30/06/2026          21 390 000     Droit commun   ▲ À valider       10/08 réduction acompte
 NOVA SERVICES SA    Services   30/06/2026                   —     —              ○ En préparation  —
 …
 ─────────────────────────────────────────────────────────────────────────────────────────────────
 Cliquez sur une ligne pour ouvrir le dossier.
```

- **Un tableau triable**, et non des cartes : c'est ainsi qu'un cabinet parcourt 30 dossiers.
- Filtres par état sous forme de boutons segmentés ; recherche sur le nom du client.
- **Collaborateur** : ses dossiers. **Expert** : tous, trié par défaut sur « À valider » puis sur l'échéance.
- Données : un résumé léger par dossier (`ResumeDossier`).

### E05 — Synthèse du dossier

```
 BATI-PLUS SARL · IS 2026 · BTP · balance au 30/06/2026                ▲ À valider    Resp. Salim A.
 [Synthèse] [1 Balance ✓] [2 Hypothèses ✓] [3 Retraitements ✓] [4 Calcul ✓] [5 Leviers ✓] [6 Acomptes ✓] [7 Livrer ▲]
 ─────────────────────────────────────────────────────────────────────────────────────────────────
  Résultat fiscal          IS dû                     Gain du scénario retenu
  71 300 000               21 390 000                3 090 000
  après retraitements      droit commun (art. 46)    décalage d'impôt (L01)

 Points d'attention
  ▲ 4 règles « à valider » utilisées : R03, R05, R16, R21                       [Voir]
  ▲ Balance déséquilibrée de 1 200 FCFA (écart accepté à l'import)             [Voir la balance]
  ⓘ Réduction d'acompte proposée : demande à déposer avant le 10/08/2026         [Voir]
  ⓘ 2 propositions de l'agent acceptées sur 4                                    [Voir]

 Derniers événements                                                         [Journal complet]
  12/10 14:02  Salim A.  Dossier soumis à validation
  12/10 13:55  Salim A.  Scénario A retenu (L01)
  12/10 11:20  Salim A.  Calcul effectué
 ─────────────────────────────────────────────────────────────────────────────────────────────────
                                                     [Renvoyer avec commentaire]   [Valider le dossier]
```

- 3 indicateurs, et non 4 : on ne garde que ceux dont dépend la décision.
- L'historique n'est plus une colonne permanente : on voit les 3 derniers événements, avec un lien vers le journal.
- Boutons Valider / Renvoyer visibles pour l'expert seulement, sur un dossier « À valider ». Valider ouvre une **confirmation**.

### E08 — Retraitements

```
 [Synthèse] [1 Balance ✓] [2 Hypothèses ✓] [3 Retraitements ▲] [4 Calcul] …
 ─────────────────────────────────────────────────────────────────────────────────────────────────
 Retraitements                                                      3 saisies à compléter sur 28
 Passage du résultat comptable au résultat fiscal (CGI art. 15 à 43).

 Catégorie : [ Toutes ] [ Non déductibles ] [ Plafonnées ] [ Conditions ] [ Déductions ]   ☐ Seulement à compléter

 Réf.  Règle                                    Article    Origine   Base (FCFA)   Retenu (FCFA)  Statut
 ─────────────────────────────────────────────────────────────────────────────────────────────────
 R01   IS comptabilisé (compte 89)              art. 35    Balance     4 500 000      4 500 000   ✓
 R02   Amendes fiscales (compte 647)            art. 36    Balance       320 000        320 000   ✓
 R13   Autres amendes (sociales, douane)        art. 36    Saisie              —              —   ▲ à compléter
 R03   Dons au-delà de 1 ‰ du CA HT             art. 32-1  Balance     2 100 000      1 950 000   ✓
 …
 ─────────────────────────────────────────────────────────────────────────────────────────────────
                                          Total réintégrations   10 240 000    Total déductions  0

 ┌ Détail de la ligne sélectionnée : R13 — Autres amendes (sociales, douanières, prix, changes) ───┐
 │ Article 36 · Règle à valider par le cabinet                                  [Lire l'article]   │
 │ Où trouver l'information : grand livre des comptes 658 et 83 ; avis de pénalités CNSS, douane.  │
 │ Montant (FCFA)  [            0 ]    ( ) Montant   (•) Néant                                      │
 │                                                                         [Enregistrer]           │
 └──────────────────────────────────────────────────────────────────────────────────────────────────┘

 Hors résultat fiscal : droit de timbre sur paiements en espèces   45 000 FCFA (art. 21, 423-4)
```

- Principe **maître-détail** : on choisit une ligne dans le tableau, et le détail s'affiche dessous. On évite ainsi 28 cartes dépliables.
- Le filtre « Seulement à compléter » permet de traiter le travail restant en une passe.

### E10 — Leviers et propositions de l'agent

```
 [Synthèse] … [4 Calcul ✓] [5 Leviers ▲] [6 Acomptes] [7 Livrer]
 ─────────────────────────────────────────────────────────────────────────────────────────────────
 Leviers avant clôture
 Chiffrer les options légales encore ouvertes avant le 31/12/2026.

 Position de départ :  IS droit commun 21 390 000 · Minimum de perception 4 700 000 · Seuil de bascule 15 700 000
 ⓘ Le résultat est au-dessus du seuil : réduire le résultat réduit l'impôt.

 ┌ LEVIERS (8/12) ─────────────────────────────────────────────┐ ┌ PROPOSITIONS DE L'AGENT (4/12) ──┐
 │ Levier                           Article  Statut     Gain    │ │ [Demander des propositions]      │
 │ ─────────────────────────────────────────────────────────── │ │                                   │
 │ L01 Amortissement dégressif      art. 40  Simulé  3 090 000  │ │ 1 · Levier chiffré · art. 41      │
 │ L02 Amortissement accéléré       art. 39  —             —    │ │   Provision pour le litige        │
 │ L03 Provision justifiée          art. 41  Proposé       —    │ │   client signalé en hypothèses.   │
 │ L04 Marge de dons                art. 32  —             —    │ │   Gain (moteur) : 1 200 000       │
 │                                                              │ │   Confiance 0,94 · risque 1/4     │
 │ L05 Charges anticipées           art. 20  —             —    │ │   [Écarter…]   [Accepter]         │
 │                                                              │ │                                   │
 │ ── L01 Amortissement dégressif (art. 40) ──────────────────  │ │ 2 · Piste à étudier · art. 17     │
 │ Montant HT (FCFA)  [ 30 000 000 ]   Durée [ 5 ans ▾ ]        │ │   Plus-value de cession avec      │
 │ Mois d'acquisition [ septembre ▾ ]                           │ │   engagement de réinvestir.       │
 │ Conditions légales :                                         │ │   Non chiffrée.                   │
 │  ☑ Matériel neuf  ☑ Valeur unitaire ≥ 10 M HT  ☑ Durée > 3 ans│ │   [Écarter…]   [Accepter]         │
 │                                                              │ │                                   │
 │             Avant        Après       Écart                   │ │ Proposé par IA : à vérifier.      │
 │ Résultat    71 300 000   61 000 000  −10 300 000             │ │ Montants recalculés par le moteur.│
 │ IS dû       21 390 000   18 300 000   −3 090 000 (décalage)  │ │ Modèle · 12 s · profil anonymisé  │
 │                                     [Enregistrer le scénario]│ │                                   │
 └──────────────────────────────────────────────────────────────┘ └───────────────────────────────────┘

 Scénarios : A (L01) ✓ retenu · B (L01 + L03)                                   [Retenir le scénario B]
```

- **Maître-détail** à gauche : la liste des leviers en tableau, le levier sélectionné paramétré dessous.
- Sous chaque proposition, la **confiance** et le **risque** viennent du modèle de décision (Jev). Sous le seuil, le badge « ▲ Confiance faible » s'affiche (texte + icône).
- **Panneau de l'agent** à droite (UC14) : il est séparé visuellement, pour qu'on distingue toujours
  ce qui vient de l'IA de ce qui vient du moteur. Les montants affichés sous une proposition sont
  ceux du moteur.
- Une proposition acceptée de type « levier » se range dans la liste de gauche (statut « Proposé »),
  déjà paramétrée.

### E14 — Assistant CGI

```
 Assistant CGI
 Retrouver et comprendre un article du CGI 2026 ou du LPF 2024.
 ─────────────────────────────────────────────────────────────────────────────────────────────────
 Question  [ Quel est le plafond de déduction des cadeaux publicitaires ?                ] [Chercher]
 ⓘ Ne saisissez ni nom de client ni montant : la question est envoyée à un service d'IA en ligne.

 ┌ ARTICLES TROUVÉS (8/12) ─────────────────────────────────┐ ┌ PROPOSITION DE RÉPONSE (4/12) ───┐
 │ CGI art. 32 · Impôt sur les sociétés          ■■■■□      │ │ Générée par IA, à vérifier dans  │
 │ « … dans la limite de 3 ‰ du chiffre d'affaires … »     │ │ les articles cités.               │
 │                                       [Lire l'article]   │ │                                   │
 │ CGI art. 20 · Impôt sur les sociétés          ■■■□□      │ │ Les cadeaux et objets            │
 │ …                                                        │ │ publicitaires sont déductibles    │
 └──────────────────────────────────────────────────────────┘ │ dans la limite de 3 ‰ du CA HT.  │
                                                              │ Article(s) : 32                   │
                                                              └───────────────────────────────────┘
```

- Les articles s'affichent **tout de suite** (recherche locale) ; la réponse de l'IA arrive à côté,
  avec un indicateur de chargement. L'écran reste donc utile même sans IA.

### E15 — Référentiel des règles

```
 Référentiel des règles — 2026                                       Validées : 6 / 28
 Règles appliquées par le moteur. L'expert-comptable valide chaque règle sur un cas chiffré.
 ─────────────────────────────────────────────────────────────────────────────────────────────────
 Statut : [ Toutes ] [ À valider 22 ] [ Validées 6 ]       Catégorie : [ Toutes ▾ ]

 Réf.  Règle                                   Article    Type            Statut
 ─────────────────────────────────────────────────────────────────────────────────────────────────
 R01   IS comptabilisé                         art. 35    Totalité        ✓ Validée (Expert, 13/10)
 R03   Dons au-delà de 1 ‰ du CA HT            art. 32-1  Plafond sur CA  ▲ À valider
 …
 ── R03 Dons au-delà de 1 ‰ du CA HT ─────────────────────────────────────────────────────────────
 Comptes : 6581, 6588 · Sens : réintégration · Source : CGI 2026          [Lire l'article 32]
 Cas chiffré :  Dons comptabilisés 2 100 000 · CA 150 000 000 · Plafond 150 000 → Réintégration 1 950 000
 Commentaire [__________________________________]                         [Valider la règle]
 Historique : aucune validation.

 [Périmètre de l'outil]  (repliable : ce qui est couvert, non couvert, hypothèses)
```

- Même modèle maître-détail que les retraitements : l'utilisateur apprend un seul schéma d'écran.
- Le bouton « Valider la règle » n'existe que pour l'expert.

### Récapitulatif des schémas d'écran

Pour la cohérence, l'application n'utilise que **trois schémas d'écran** :

| Schéma | Écrans |
|---|---|
| **Liste** (tableau + filtres) | E03 Dossiers, E16 Journal, E17 Utilisateurs |
| **Maître-détail** (tableau + panneau du détail sélectionné) | E08 Retraitements, E10 Leviers, E15 Référentiel, E06 Balance (comptes lus) |
| **Formulaire** (sections + une action principale) | E01 Connexion, E04 Création, E07 Hypothèses, E11 Acomptes, E12 Soumission, E13 Livrables |

E05 (Synthèse) et E14 (Assistant) sont les deux seuls écrans spécifiques.

---

## Partie C — Circulation des données entre l'interface et le domaine

### C.1 Le principe

```
      ÉCRAN (Streamlit)                 APPLICATION                     DOMAINE
  ┌─────────────────────┐   commande  ┌────────────────────┐  appelle  ┌──────────────┐
  │ widgets → valeurs   │ ──────────▶ │ cas d'usage        │ ────────▶ │ objets purs  │
  │ brutes (texte,      │             │ - vérifie le droit │           │ + calculs    │
  │ nombre, fichier)    │             │ - charge (ports)   │ ◀──────── │              │
  │                     │ ◀────────── │ - orchestre        │  résultat └──────────────┘
  │ formate et affiche  │  résultat   │ - enregistre/trace │
  └─────────────────────┘  (immuable) └────────────────────┘
                                             │ ▲ ports
                                             ▼ │
                                       INFRASTRUCTURE (SQLite, YAML, Excel, OpenRouter)
```

Les **cinq règles** de circulation :

1. **Vers le métier, l'écran envoie une « commande »** : un petit objet qui regroupe les saisies, par
   exemple `SaisieRetraitement(id_dossier, id_regle, montant: Decimal | None, neant: bool)`. La
   conversion du texte saisi (« 1 500 000 ») en `Decimal` est faite par un **composant de saisie
   unique**, testé une fois pour toutes.
2. **Du métier, l'écran reçoit un objet immuable** (`ResultatFiscal`, `RapportLecture`…). Il ne peut
   pas le modifier, seulement l'afficher.
3. **Le formatage est fait à l'affichage, et seulement là.** Le domaine manipule `Decimal("36800000")` ;
   l'écran affiche `36,8 M FCFA`. Les fonctions de formatage vivent dans `interface/`.
4. **Les erreurs métier sont des exceptions typées** (`BalanceIllisible`, `AccesRefuse`,
   `DossierFige`…). L'écran les attrape et affiche un message clair, jamais une trace Python.
5. **`st.session_state` ne contient que des identifiants et des préférences d'affichage** :
   l'utilisateur connecté, l'id du dossier ouvert, l'onglet choisi. **Jamais de résultat de
   calcul.** La source de vérité, c'est la base, lue via l'Application. Cela évite un défaut de la
   V2 : un écran qui affichait un résultat périmé gardé en mémoire.

### C.2 Exemple détaillé : import d'une balance (UC01)

```
Collaborateur      Écran E06                ImporterBalance             LecteurBalance (infra)     DepotDossiers (infra)   Journal
     │ dépose fichier │                            │                            │                         │                   │
     │───────────────▶│                            │                            │                         │                   │
     │                │ lire(octets, nom, date)    │                            │                         │                   │
     │                │───────────────────────────▶│ exiger droit               │                         │                   │
     │                │                            │ lire(octets, nom)          │                         │                   │
     │                │                            │───────────────────────────▶│ Excel → lignes → Decimal│                   │
     │                │                            │◀───────────────────────────│ Balance + RapportLecture│                   │
     │                │                            │ contrôler(balance) (domaine)                         │                   │
     │                │◀───────────────────────────│ ApercuImport (non enregistré)                        │                   │
     │ lit le rapport │                            │                            │                         │                   │
     │ « Confirmer »  │                            │                            │                         │                   │
     │───────────────▶│ confirmer(id_apercu)       │                            │                         │                   │
     │                │───────────────────────────▶│ enregistrer_balance(...)   │                         │                   │
     │                │                            │─────────────────────────────────────────────────────▶│                   │
     │                │                            │ tracer("Balance importée : 412 comptes")                                 │
     │                │                            │─────────────────────────────────────────────────────────────────────────▶│
     │                │◀───────────────────────────│ OK, état = EN PRÉPARATION  │                         │                   │
     │ voit ✓ Balance │                            │                            │                         │                   │
```

Ce qu'il faut retenir : l'import se fait en **deux temps** (aperçu, puis confirmation). Rien n'est
enregistré tant que le collaborateur n'a pas lu le rapport de lecture.

### C.3 Ce que chaque écran lit et écrit

| Écran | Lit (via l'Application) | Écrit (commande) |
|---|---|---|
| E03 Tableau de bord | `ResumeDossier[]` | — |
| E04 Création | listes fermées (secteurs, taux) | `CreerDossier` |
| E05 Vue dossier | `VueDossier` (résumé, étapes, alertes, 10 derniers événements) | `ValiderDossier`, `RenvoyerDossier` |
| E06 Balance | `ApercuImport`, `RapportLecture` | `ImporterBalance`, `ConfirmerImport` |
| E07 Hypothèses | `HypothesesProjection`, aperçu de la projection | `DefinirHypotheses` |
| E08 Retraitements | `LigneRetraitement[]`, règles et statuts | `SaisieRetraitement` |
| E09 Calcul | `ResultatFiscal` (piste d'audit comprise) | `CalculerIsPrevisionnel` |
| E10 Leviers | leviers et conditions, `Scenario[]`, `Proposition[]` | `SimulerScenario`, `RetenirScenario`, `DemanderPropositions`, `DeciderProposition` |
| E11 Acomptes | `Echeancier` | `DeciderAcomptes` |
| E12 Soumission | liste de contrôle | `SoumettreDossier` |
| E13 Livrables | liste des fichiers générés | `GenererLivrables` |
| E14 Assistant | `Article[]`, `ReponseAssistant` | `PoserQuestion` |
| E15 Référentiel | règles, validations, cas chiffrés | `ValiderRegle` |
| E16 Journal | `EvenementAudit[]` | — |
| E17 Utilisateurs | `Utilisateur[]` | `CreerUtilisateur`, `ChangerRole`, `Desactiver` |

---

## Décisions à valider

- [ OUI ] **D5.1** Design system de la V2 conservé (statut par la couleur, bleu réservé aux actions, sobriété, hors ligne).
- [ ✔ Révisé le 14/10 (commentaire d'origine : « A revoire ») ] **D5.2** Maquettes E03, E05, E08, E10, E14 et E15 comme base de l'intégration Streamlit.
- [ OUI ] **D5.6** (nouveau) Diagnostic A.1 et principes A.2 : natif Streamlit d'abord, une action principale par écran, tableaux plutôt que cartes, mode clair uniquement.
- [ OUI ] **D5.7** (nouveau) Palette A.3 (marine + bleu d'action) et trois schémas d'écran (liste, maître-détail, formulaire). **Révisée le 17/10/2026** : accent vert, cartes blanches sur fond menthe (A.3 révisé).
- [ OUI ] **D5.9** (17/10) Graphiques avec retenue (Altair, skill dataviz) : jauge d'avancement, emphase de l'impôt appliqué, cascade du résultat fiscal, acomptes. Toujours un tableau à côté.
- [ À valider ] **D5.10** (17/10) Typographie Plus Jakarta Sans + Inter hébergées localement ; icônes Material ; logo professionnel fourni par Salim.
- [ OUI ] **D5.8** (nouveau) Panneau « Propositions de l'agent » séparé visuellement sur l'écran Leviers (E10).
- [ OUI ] **D5.3** Les cinq règles de circulation (C.1), en particulier : pas de résultat de calcul dans `session_state`.
- [ OUI ] **D5.4** Import de balance en deux temps (aperçu, puis confirmation).
- [ OUI ] **D5.5** Avertissement permanent sur l'écran Assistant concernant l'envoi en ligne.
