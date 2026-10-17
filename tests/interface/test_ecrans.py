"""J9-J10 — test de fumée de l'interface : chaque écran s'affiche sans erreur (AppTest, sans navigateur).

L'application tourne en mode démonstration sur une base temporaire, avec un mot de passe de démo connu.
"""
from decimal import Decimal
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from optifisc.interface.streamlit import etat

APP = Path(__file__).resolve().parents[2] / "src" / "optifisc" / "interface" / "streamlit" / "app.py"
MOT_DE_PASSE = "Demo#Soutenance26"
ETAPES = ["synthese", "balance", "hypotheses", "retraitements", "calcul", "leviers", "acomptes", "livrer"]


@pytest.fixture(scope="module")
def environnement(tmp_path_factory):
    mp = pytest.MonkeyPatch()
    mp.setenv("OPTIFISC_MODE", "demo")
    mp.setenv("OPTIFISC_BASE", str(tmp_path_factory.mktemp("ui") / "demo.sqlite"))
    mp.setenv("OPTIFISC_MDP_DEMO", MOT_DE_PASSE)
    yield
    mp.undo()


def page_de_connexion() -> AppTest:
    """L'application s'ouvre sur l'accueil ; la connexion est la page suivante."""
    at = AppTest.from_file(str(APP), default_timeout=60).run()
    return at.switch_page("app_pages/connexion.py").run()


def bouton_se_connecter(at: AppTest):
    return next(b for b in at.button if b.label == "Se connecter")


def connecte(email: str) -> AppTest:
    at = page_de_connexion()
    at.text_input[0].input(email)
    at.text_input[1].input(MOT_DE_PASSE)
    bouton_se_connecter(at).click().run()
    assert not at.exception, at.exception
    return at


def test_accueil_avant_connexion(environnement):
    at = AppTest.from_file(str(APP), default_timeout=60).run()
    assert not at.exception, at.exception
    assert "Piloter l'IS" in at.title[0].value
    assert any(b.label == "Se connecter" for b in at.button)


def test_ecran_de_connexion(environnement):
    at = page_de_connexion()
    assert not at.exception
    assert at.header[0].value == "Connexion"


def test_mauvais_mot_de_passe_refuse(environnement):
    at = page_de_connexion()
    at.text_input[0].input("salim@demo.bj")
    at.text_input[1].input("mauvais")
    bouton_se_connecter(at).click().run()
    assert any("incorrect" in e.value for e in at.error)


def test_tableau_de_bord_et_toutes_les_etapes_du_dossier(environnement):
    at = connecte("salim@demo.bj")
    assert at.header[0].value == "Dossiers"
    assert len(at.dataframe) == 1
    # préparer le premier dossier jusqu'au calcul, pour que toutes les étapes soient accessibles
    app = etat.application()
    salim = app.comptes.utilisateur_actif("salim@demo.bj")
    dossier_id = app.dossiers.lister(salim)[0].dossier.id
    for ligne in app.calcul.resultat(salim, dossier_id).retraitements:
        if not ligne.renseignee:
            app.dossiers.saisir(salim, dossier_id, ligne.id_regle, Decimal(0))
    app.calcul.calculer(salim, dossier_id)
    at.session_state["dossier_id"] = dossier_id
    for etape in ETAPES:
        at.session_state["etape"] = etape
        at.switch_page("app_pages/dossier.py").run()
        assert not at.exception, (etape, at.exception)
        assert not any("pas encore accessible" in i.value for i in at.info), etape


@pytest.mark.parametrize("page", ["app_pages/referentiel.py", "app_pages/journal.py", "app_pages/profil.py",
                                  "app_pages/assistant.py", "app_pages/missions.py", "app_pages/accueil.py"])
def test_pages_outils(environnement, page):
    at = connecte("expert@demo.bj")
    at.switch_page(page).run()
    assert not at.exception, at.exception


def test_page_utilisateurs_pour_l_administrateur(environnement):
    at = connecte("admin@demo.bj")
    at.switch_page("app_pages/utilisateurs.py").run()
    assert not at.exception, at.exception
    assert len(at.dataframe) >= 1


def test_connexion_rapide_et_changement_de_role_en_demo(environnement):
    at = page_de_connexion()
    at.button(key="demo_expert").click().run()
    assert not at.exception and at.header[0].value == "Dossiers"
    assert etat.application().comptes.utilisateur_actif(at.session_state["email"]).role.value == "expert"


@pytest.mark.parametrize("email", ["salim@demo.bj", "expert@demo.bj", "admin@demo.bj"])
def test_journal_de_missions_de_chaque_role(environnement, email):
    at = connecte(email)
    at.switch_page("app_pages/missions.py").run()
    assert not at.exception, at.exception
    assert at.header[0].value == "Mes missions"
    assert any(m.value.startswith("#### Mission 1") for m in at.markdown)
