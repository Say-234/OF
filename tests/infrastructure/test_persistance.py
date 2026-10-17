"""J7 — persistance SQLite : aller-retour exact des Decimal, journal en ajout seul, sécurité des mots de passe."""
import sqlite3
from datetime import date, datetime
from decimal import Decimal

import pytest

from conftest import balance, dossier
from optifisc.domaine.balance import RapportLecture
from optifisc.domaine.dossier import EtatDossier
from optifisc.domaine.journal import EvenementAudit
from optifisc.domaine.scenario import LevierChoisi, Scenario
from optifisc.domaine.utilisateur import Role, Utilisateur
from optifisc.infrastructure.persistance.connexion import BaseSqlite
from optifisc.infrastructure.persistance.depots import (
    DepotBalancesSqlite,
    DepotDonneesDossierSqlite,
    DepotDossiersSqlite,
    DepotPreferencesSqlite,
    DepotScenariosSqlite,
    DepotUtilisateursSqlite,
    DepotValidationsSqlite,
    JournalSqlite,
)
from optifisc.infrastructure.securite import MotsDePassePbkdf2

QUAND = datetime(2026, 10, 16, 10, 30)


@pytest.fixture
def base(tmp_path):
    return BaseSqlite(tmp_path / "test.sqlite")


def test_migrations_appliquees_une_seule_fois(tmp_path):
    chemin = tmp_path / "b.sqlite"
    BaseSqlite(chemin)
    BaseSqlite(chemin)                                       # une deuxième ouverture ne rejoue pas le schéma
    with sqlite3.connect(chemin) as cx:
        assert cx.execute("PRAGMA user_version").fetchone()[0] == 2   # 001 schéma, 002 préférences


def test_dossier_aller_retour_exact(base):
    depot = DepotDossiersSqlite(base)
    d = dossier("btp", saisies={"R06_TVM": 1_234_567}, mois_arrete=6, is_n_moins_1=52_000_000,
                ajustements=[("6813", 45_000_000)])
    depot.enregistrer(d)
    relu = depot.charger("test")
    assert relu == d
    assert isinstance(relu.saisies["R06_TVM"], Decimal)
    depot.enregistrer(relu.vers(EtatDossier.EN_PREPARATION))
    assert depot.charger("test").etat is EtatDossier.EN_PREPARATION
    assert len(depot.lister()) == 1


def test_balance_aller_retour_et_historique(base):
    DepotDossiersSqlite(base).enregistrer(dossier())
    depot = DepotBalancesSqlite(base)
    b1 = balance(("601", "Achats", 10, 0))
    b2 = balance(("601", "Achats", 20, 0), ("701", "Ventes", 0, "12345.67"))
    rapport = RapportLecture(fichier="b.xlsx", regroupements_ignores=("60",))
    depot.enregistrer("test", b1, rapport, date(2026, 6, 30), "salim@cabinet.bj", QUAND)
    depot.enregistrer("test", b2, rapport, date(2026, 6, 30), "salim@cabinet.bj", QUAND)
    relue, rapport_relu, arrete = depot.derniere("test")
    assert relue == b2 and rapport_relu == rapport and arrete == date(2026, 6, 30)


def test_donnees_scenarios_validations(base):
    DepotDossiersSqlite(base).enregistrer(dossier())
    donnees = DepotDonneesDossierSqlite(base)
    donnees.sauver("test", "acomptes", {"decision": "demande", "montant": "0"})
    assert donnees.lire("test", "acomptes")["decision"] == "demande"
    scenarios = DepotScenariosSqlite(base)
    s = Scenario("s1", "test", "A", (LevierChoisi("L03_PROVISION_JUSTIFIEE", {"montant": "5000000"}),),
                 Decimal(1_500_000), True)
    scenarios.enregistrer(s)
    assert scenarios.lister("test") == [s]
    validations = DepotValidationsSqlite(base)
    validations.valider("R01_IS_COMPTABILISE", "abc123", "expert@cabinet.bj", "cas", "ok", QUAND)
    assert validations.lister()["R01_IS_COMPTABILISE"]["valide_par"] == "expert@cabinet.bj"


def test_journal_en_ajout_seul(base):
    journal = JournalSqlite(base)
    journal.ajouter(EvenementAudit(QUAND, "salim@cabinet.bj", "collaborateur", "balance_importee", "412 comptes",
                                   "test"))
    assert journal.lister("test")[0].action == "balance_importee"
    with base.connexion() as cx, pytest.raises(sqlite3.DatabaseError, match="ajout seul"):
        cx.execute("DELETE FROM journal")
    with base.connexion() as cx, pytest.raises(sqlite3.DatabaseError, match="ajout seul"):
        cx.execute("UPDATE journal SET detail = 'falsifié'")


def test_requetes_parametrees_resistent_a_l_injection(base):
    depot = DepotDossiersSqlite(base)
    depot.enregistrer(dossier())
    assert depot.charger("test' OR '1'='1") is None


# ------------------------------------------------------------------ utilisateurs et mots de passe
def test_utilisateur_et_mot_de_passe_hache(base):
    service = MotsDePassePbkdf2()
    depot = DepotUtilisateursSqlite(base)
    sel, empreinte = service.hacher("Cabinet#2026")
    depot.ajouter(Utilisateur("expert@cabinet.bj", "Expert", Role.EXPERT), sel, empreinte)
    sel_lu, empreinte_lue = depot.identifiants("expert@cabinet.bj")
    assert "Cabinet#2026" not in empreinte_lue                # le mot de passe n'est jamais stocké
    assert service.verifier("Cabinet#2026", sel_lu, empreinte_lue)
    assert not service.verifier("mauvais", sel_lu, empreinte_lue)
    depot.noter_connexion("expert@cabinet.bj", 3, QUAND, None)
    assert depot.etat_connexion("expert@cabinet.bj") == (3, QUAND)


@pytest.mark.parametrize("mot_de_passe, acceptable", [("court", False), ("12345678", False), ("demo2026", False),
                                                      ("Cabinet#2026", True), ("huitcara", True)])
def test_politique_de_mot_de_passe_8_caracteres(mot_de_passe, acceptable):
    assert (MotsDePassePbkdf2().probleme(mot_de_passe) is None) == acceptable


def test_mot_de_passe_genere_respecte_la_politique():
    service = MotsDePassePbkdf2()
    assert service.probleme(service.generer()) is None


def test_preferences_par_utilisateur(base):
    depot = DepotPreferencesSqlite(base)
    assert depot.lire("a@x.bj", "tutoriel") is None
    depot.sauver("a@x.bj", "tutoriel", {"vu": True, "faites": ["journal"]})
    depot.sauver("a@x.bj", "tutoriel", {"vu": True, "faites": []})          # remplace, ne duplique pas
    assert depot.lire("a@x.bj", "tutoriel") == {"vu": True, "faites": []}
    assert depot.lire("b@x.bj", "tutoriel") is None
