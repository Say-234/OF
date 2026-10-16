# Journal de bord

> À lire **en premier** au début de chaque session, par Salim ou par n'importe quel agent IA.
> À mettre à jour **à la fin** de chaque session. L'entrée la plus récente est en haut.

## État actuel

| | |
|---|---|
| **Phase** | Conception (documents 00 à 06) — presque terminée |
| **Jalon en cours** | Aucun : J0 pas encore commencé |
| **Prochaine action** | Salim relit les décisions restantes (D1.7, D1.8, D3.6 à D3.8, D5.6 à D5.8, D6.7 à D6.9), puis on lance **J0 — Poste de travail** |
| **Tests** | Pas encore de code |
| **Retard sur le calendrier** | J0 était prévu le 14/10, il glisse au 15/10 : surveiller (plan de repli au-delà d'un jour) |

## Questions ouvertes

- Format exact d'appel de Jev via OpenRouter, sa tenue en français, ses conditions d'accès (à vérifier à J11).
- Conditions de l'offre gratuite de Streamlit Community Cloud : dépôt privé, mise en veille (à vérifier à J12).
- Balance réelle anonymisée : à obtenir auprès du cabinet pour la recette (J12).

---

## Historique des sessions

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
