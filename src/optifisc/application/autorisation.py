"""Matrice des droits (doc 02, §4), en mode « fail-closed » : ce qui n'est pas permis est refusé.

La matrice est écrite ICI, une seule fois, et non dans un fichier modifiable. Chaque cas
d'usage appelle exiger() AVANT d'agir : masquer un bouton à l'écran n'est pas une protection.
"""
from optifisc.domaine.dossier import Dossier
from optifisc.domaine.erreurs import AccesRefuse
from optifisc.domaine.utilisateur import Role, Utilisateur

C, E, A = Role.COLLABORATEUR, Role.EXPERT, Role.ADMIN

MATRICE: dict[str, set[Role]] = {
    "voir_dossier": {C, E, A},
    "creer_dossier": {C, E},
    "preparer_dossier": {C, E},            # importer la balance, saisir, calculer, simuler
    "soumettre_dossier": {C, E},
    "valider_dossier": {E},
    "rouvrir_dossier": {E},
    "livrables_provisoires": {C, E},
    "livrables_definitifs": {E},
    "valider_regle": {E},
    "consulter_journal": {C, E, A},
    "gerer_utilisateurs": {A},
    "attribuer_dossier": {E, A},
    "interroger_assistant": {C, E, A},
    "demander_propositions": {C, E},
}

# Pour ces actions, un collaborateur n'agit que sur les dossiers qui lui sont attribués (cloisonnement).
LIMITEES_A_SES_DOSSIERS = {"voir_dossier", "preparer_dossier", "soumettre_dossier", "livrables_provisoires",
                           "consulter_journal", "demander_propositions"}


def peut(utilisateur: Utilisateur | None, action: str, dossier: Dossier | None = None) -> bool:
    if utilisateur is None or not utilisateur.actif:
        return False
    roles = MATRICE.get(action)
    if roles is None or utilisateur.role not in roles:        # action inconnue : refusée
        return False
    if utilisateur.role is Role.COLLABORATEUR and action in LIMITEES_A_SES_DOSSIERS and dossier is not None:
        return dossier.responsable == utilisateur.email
    return True


def exiger(utilisateur: Utilisateur | None, action: str, dossier: Dossier | None = None) -> None:
    if not peut(utilisateur, action, dossier):
        raise AccesRefuse("Accès refusé : vous n'avez pas le droit de faire cette action.")
