# Journal de bord

> À lire **en premier** au début de chaque session, par Salim ou par n'importe quel agent IA.
> À mettre à jour **à la fin** de chaque session. L'entrée la plus récente est en haut.

## État actuel

| | |
|---|---|
| **Phase** | Construction (l'agent construit, Salim supervise à la fin — décision du 16/10/2026) |
| **Jalon en cours** | J6 — leviers et acomptes |
| **Prochaine action** | Terminer J6, puis J7 (persistance SQLite) |
| **Tests** | 81 verts (`.venv/Scripts/python -m pytest -q`) ; ruff propre |
| **Retard sur le calendrier** | Rattrapé : J0 à J5 faits le 16/10 |

## Questions ouvertes

- Format exact d'appel de Jev via OpenRouter, sa tenue en français, ses conditions d'accès (à vérifier à J11).
- Conditions de l'offre gratuite de Streamlit Community Cloud : dépôt privé, mise en veille (à vérifier à J12).
- Balance réelle anonymisée : à obtenir auprès du cabinet pour la recette (J12).

---

## Historique des sessions

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
