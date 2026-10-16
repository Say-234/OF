"""J8 — matrice des droits (fail-closed, cloisonnement) et connexion (blocage après 5 échecs)."""
from dataclasses import replace
from datetime import datetime, timedelta

import pytest

from conftest import dossier
from optifisc.application.autorisation import MATRICE, exiger, peut
from optifisc.application.comptes import ServiceComptes
from optifisc.domaine.erreurs import AccesRefuse, DonneeInvalide
from optifisc.domaine.utilisateur import Role, Utilisateur
from optifisc.infrastructure.persistance.connexion import BaseSqlite
from optifisc.infrastructure.persistance.depots import DepotUtilisateursSqlite, JournalSqlite
from optifisc.infrastructure.securite import MotsDePassePbkdf2

SALIM = Utilisateur("salim@cabinet.bj", "Salim", Role.COLLABORATEUR)
AUTRE = Utilisateur("autre@cabinet.bj", "Autre", Role.COLLABORATEUR)
EXPERT = Utilisateur("expert@cabinet.bj", "Expert", Role.EXPERT)
ADMIN = Utilisateur("admin@cabinet.bj", "Admin", Role.ADMIN)
DOSSIER_DE_SALIM = replace(dossier(), responsable=SALIM.email)


# ------------------------------------------------------------------ matrice des droits
def test_action_inconnue_refusee_fail_closed():
    for u in (SALIM, EXPERT, ADMIN):
        assert not peut(u, "action_qui_n_existe_pas")


def test_personne_non_connectee_ou_desactivee_refusee():
    assert not peut(None, "voir_dossier")
    assert not peut(replace(EXPERT, actif=False), "valider_dossier")


def test_cloisonnement_un_collaborateur_ne_voit_que_ses_dossiers():
    assert peut(SALIM, "preparer_dossier", DOSSIER_DE_SALIM)
    assert not peut(AUTRE, "preparer_dossier", DOSSIER_DE_SALIM)
    assert peut(EXPERT, "preparer_dossier", DOSSIER_DE_SALIM)


def test_seul_l_expert_valide():
    for action in ("valider_dossier", "rouvrir_dossier", "livrables_definitifs", "valider_regle"):
        assert MATRICE[action] == {Role.EXPERT}
        assert not peut(SALIM, action, DOSSIER_DE_SALIM) and not peut(ADMIN, action)


def test_separation_admin_et_fiscal():
    assert peut(ADMIN, "gerer_utilisateurs")
    assert not peut(ADMIN, "preparer_dossier", DOSSIER_DE_SALIM)
    assert not peut(EXPERT, "gerer_utilisateurs")


def test_exiger_leve_acces_refuse():
    with pytest.raises(AccesRefuse):
        exiger(SALIM, "valider_dossier", DOSSIER_DE_SALIM)


# ------------------------------------------------------------------ connexion
class HorlogeFigee:
    def __init__(self):
        self.instant = datetime(2026, 10, 16, 9, 0)

    def maintenant(self):
        return self.instant

    def aujourd_hui(self):
        return self.instant.date()


@pytest.fixture
def comptes(tmp_path):
    base = BaseSqlite(tmp_path / "t.sqlite")
    service = ServiceComptes(DepotUtilisateursSqlite(base), MotsDePassePbkdf2(), JournalSqlite(base), HorlogeFigee())
    service.journal_brut = JournalSqlite(base)
    return service


def test_premier_administrateur_puis_creation_de_compte(comptes):
    mdp_admin = comptes.creer_premier_administrateur("admin@cabinet.bj", "Admin")
    admin = comptes.connecter("admin@cabinet.bj", mdp_admin)
    assert admin.doit_changer_mot_de_passe                       # mot de passe initial à changer
    mdp = comptes.creer_utilisateur(admin, "salim@cabinet.bj", "Salim", Role.COLLABORATEUR)
    assert comptes.connecter("SALIM@cabinet.bj ", mdp).role is Role.COLLABORATEUR
    with pytest.raises(AccesRefuse):
        comptes.creer_premier_administrateur("pirate@x.bj", "Pirate")   # plus possible une fois installé


def test_seul_l_admin_cree_des_comptes(comptes):
    with pytest.raises(AccesRefuse):
        comptes.creer_utilisateur(EXPERT, "x@cabinet.bj", "X", Role.EXPERT)


def test_blocage_apres_5_echecs_puis_deblocage(comptes):
    mdp = comptes.creer_premier_administrateur("admin@cabinet.bj", "Admin")
    for _ in range(5):
        with pytest.raises(AccesRefuse, match="incorrect"):
            comptes.connecter("admin@cabinet.bj", "mauvais")
    with pytest.raises(AccesRefuse, match="bloqué"):
        comptes.connecter("admin@cabinet.bj", mdp)              # même le bon mot de passe est refusé
    comptes.horloge.instant += timedelta(minutes=16)
    assert comptes.connecter("admin@cabinet.bj", mdp).email == "admin@cabinet.bj"
    actions = [e.action for e in comptes.journal_brut.lister()]
    assert "connexion_refusee" in actions and "connexion" in actions


def test_message_identique_si_le_compte_n_existe_pas(comptes):
    with pytest.raises(AccesRefuse, match="E-mail ou mot de passe incorrect"):
        comptes.connecter("inconnu@cabinet.bj", "x")


def test_changement_de_mot_de_passe_et_politique(comptes):
    mdp = comptes.creer_premier_administrateur("admin@cabinet.bj", "Admin")
    admin = comptes.connecter("admin@cabinet.bj", mdp)
    with pytest.raises(DonneeInvalide, match="8 caractères"):
        comptes.changer_mot_de_passe(admin, mdp, "court")
    admin = comptes.changer_mot_de_passe(admin, mdp, "Cabinet#2026")
    assert not admin.doit_changer_mot_de_passe
    assert comptes.connecter("admin@cabinet.bj", "Cabinet#2026")


def test_un_admin_ne_peut_pas_se_desactiver(comptes):
    mdp = comptes.creer_premier_administrateur("admin@cabinet.bj", "Admin")
    admin = comptes.connecter("admin@cabinet.bj", mdp)
    with pytest.raises(DonneeInvalide):
        comptes.modifier_utilisateur(admin, admin.email, actif=False)


def test_compte_desactive_ne_se_connecte_plus(comptes):
    admin = comptes.connecter("admin@cabinet.bj", comptes.creer_premier_administrateur("admin@cabinet.bj", "A"))
    mdp = comptes.creer_utilisateur(admin, "salim@cabinet.bj", "Salim", Role.COLLABORATEUR)
    comptes.modifier_utilisateur(admin, "salim@cabinet.bj", actif=False)
    with pytest.raises(AccesRefuse):
        comptes.connecter("salim@cabinet.bj", mdp)
