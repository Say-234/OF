"""Journal de missions : étapes cochées par les données, coches manuelles, recommencer."""
import pytest

from optifisc.application.tutoriel import ServiceTutoriel
from optifisc.composition import construire
from optifisc.domaine.utilisateur import Role, Utilisateur


@pytest.fixture
def app_demo(tmp_path, monkeypatch):
    monkeypatch.setenv("OPTIFISC_MDP_DEMO", "Demo#Soutenance26")
    return construire(tmp_path / "tuto.sqlite", mode="demo")


def test_tutoriel_suit_les_donnees_et_les_coches(app_demo):
    app = app_demo
    salim = Utilisateur("salim@demo.bj", "Salim", Role.COLLABORATEUR)
    service: ServiceTutoriel = app.tutoriel
    tuto = service.tutoriel(salim)
    assert tuto.dossier is not None and not tuto.vu
    faites = {e.id for m in tuto.missions for e in m.etapes if e.faite}
    # le dossier de démonstration est préparé jusqu'au calcul : ces étapes sont déjà cochées
    assert {"balance", "hypotheses", "retraitements", "calcul"} <= faites
    mission, etape = tuto.en_cours
    assert etape.id == "leviers" and etape.etape_dossier == "leviers"

    service.marquer_vu(salim)
    assert service.tutoriel(salim).vu


def test_coche_manuelle_et_recommencer(app_demo):
    expert = Utilisateur("expert@demo.bj", "Expert", Role.EXPERT)
    service = app_demo.tutoriel
    service.cocher(expert, "lire_synthese")
    assert next(e for m in service.tutoriel(expert).missions for e in m.etapes if e.id == "lire_synthese").faite
    service.recommencer(expert)
    tuto = service.tutoriel(expert)
    assert not tuto.vu
    assert not next(e for m in tuto.missions for e in m.etapes if e.id == "lire_synthese").faite


def test_chaque_role_a_des_missions(app_demo):
    for role in Role:
        tuto = app_demo.tutoriel.tutoriel(Utilisateur(f"{role.value}@x.bj", "X", role))
        assert tuto.total >= 4
