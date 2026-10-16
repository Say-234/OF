# OptiFisc — Dossier de conception (avant code)

Ce dossier fige **ce que l'on construit et pourquoi**, avant d'écrire la moindre ligne de code.
Il est rédigé pour être lu dans l'ordre, une section à la fois, et validé section par section.

## Le projet en une phrase

Un outil, installé sur le poste du cabinet, qui part d'une **balance générale arrêtée en cours d'année**,
estime l'**impôt sur les sociétés (IS)** de l'exercice selon le **CGI du Bénin 2026**, montre les
**leviers légaux** encore activables avant la clôture, et produit des **livrables validés par
l'expert-comptable**.

> Règle d'or du projet : **l'IA ne calcule jamais un impôt.** Tout montant sort d'un moteur de règles
> déterministe, testé, et chaque chiffre est relié à un article du CGI. L'IA retrouve et explique
> les textes, et **propose** des pistes d'optimisation ; le moteur chiffre ; l'humain décide.

## Ordre de lecture et état de validation

| # | Document | Question à laquelle il répond | Statut |
|---|---|---|---|
| 0 | [00_glossaire.md](00_glossaire.md) | Que veulent dire les mots techniques employés ? | Référence |
| 1 | [01_stack_et_architecture.md](01_stack_et_architecture.md) | Avec quels outils, et comment le code est-il rangé ? | **Validé** le 14/10/2026 ; A.3 complété pour l'agent, A.4 Laya/Jev : **à relire** D1.7, D1.8 |
| 2 | [02_acteurs_et_permissions.md](02_acteurs_et_permissions.md) | Qui utilise l'outil et qui a le droit de faire quoi ? | **Validé** le 14/10/2026 (mot de passe : 8 caractères) |
| 3 | [03_cas_utilisation.md](03_cas_utilisation.md) | Quelles actions métier l'outil permet-il ? | Révisé le 14/10 (agent IA, UC14) : **à relire** D3.6 à D3.8 |
| 4 | [04_parcours_utilisateur.md](04_parcours_utilisateur.md) | Dans quel ordre l'utilisateur passe-t-il d'un écran à l'autre ? | **Validé** le 14/10/2026 |
| 5 | [05_interfaces_et_flux.md](05_interfaces_et_flux.md) | À quoi ressemble chaque écran et comment circulent les données ? | Révisé le 14/10 (maquettes refaites) : **à relire** D5.6 à D5.8 |
| 6 | [06_plan_mvp.md](06_plan_mvp.md) | Dans quel ordre construit-on, et comment met-on en service ? | Révisé le 14/10 (calendrier, repli, démo en ligne) : **à relire** D6.7 à D6.9 |
| 7 | [07_structure_du_code.md](07_structure_du_code.md) | Où vit chaque responsabilité dans le code ? (grille de conformité) | Écarts de construction listés au §5 : **à valider** |
| 8 | [08_mise_en_service.md](08_mise_en_service.md) | Comment installer, configurer l'IA, mettre en ligne la démo, sauvegarder ? | Rédigé le 16/10/2026 |
| 9 | [09_guide_utilisateur.md](09_guide_utilisateur.md) | Qui fait quoi pour que l'outil fonctionne au cabinet ? | Rédigé le 16/10/2026 |
| 10 | [10_scenario_soutenance.md](10_scenario_soutenance.md) | Comment dérouler la démonstration le jour J ? | Rédigé le 16/10/2026 |
| — | [JOURNAL_DE_BORD.md](JOURNAL_DE_BORD.md) | Où en est le projet ? (à lire en premier à chaque session) | Tenu à jour |

## Comment valider une section

1. Lire le document en entier.
2. Répondre aux points de la rubrique **« Décisions à valider »** en fin de document (oui / non / à modifier).
3. Une fois les réponses intégrées, passer le statut à « Validé » dans le tableau ci-dessus, avec la date.

On ne passait au code qu'une fois les six sections validées (fait le 16/10/2026). Toute décision changée plus tard est notée
dans le document concerné (rubrique « Historique des décisions »), pour garder la trace du raisonnement :
c'est utile pour le mémoire et pour la soutenance.

## Sources de référence

- Code Général des Impôts du Bénin 2026, Livre des procédures fiscales 2024 (PDF dans `../../OptiFisc/`).
- Acte uniforme OHADA relatif au droit comptable (SYSCOHADA révisé).
- Deux prototypes antérieurs, conservés **en lecture seule** comme sources : `../../opti_fisc/` (V1,
  bonne architecture) et `../../OptiFisc/OptiFisc_App/` (V2, bon contenu métier). Le rapport d'audit
  qui les compare a conduit aux choix de ce dossier.
