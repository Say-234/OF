"""J2 — chargement et validation du référentiel 2026."""
import shutil
from decimal import Decimal
from pathlib import Path

import pytest

from optifisc.domaine.erreurs import ReferentielInvalide
from optifisc.domaine.referentiel import Statut, TypeRegle
from optifisc.infrastructure.referentiel_yaml import ReferentielYaml

RACINE = Path(__file__).resolve().parents[2] / "referentiel"


@pytest.fixture(scope="module")
def ref():
    return ReferentielYaml(RACINE).charger(2026)


def test_taux_lus_en_decimal_exact(ref):
    assert ref.parametres.taux_is["droit_commun"] == Decimal("0.30")
    assert isinstance(ref.parametres.taux_minimum["btp"], Decimal)
    assert ref.parametres.plancher_minimum == 250_000


def test_contenu_attendu_du_referentiel(ref):
    assert len(ref.regles) == 28
    assert {lv.id for lv in ref.leviers} >= {"L01_INVESTISSEMENT_DEGRESSIF", "L06_REDUCTION_ACOMPTES"}
    assert ref.parametres.acomptes.echeances == ((3, 10), (6, 10), (9, 10), (12, 10))
    assert ref.parametres.depot_declaration == (4, 30)


def test_chaque_regle_a_un_article_et_un_statut(ref):
    for regle in ref.regles:
        assert regle.article.startswith("CGI art."), regle.id
        assert regle.statut in (Statut.A_VALIDER, Statut.VALIDE)


def test_regles_lues_en_balance_ont_des_comptes(ref):
    for regle in ref.regles:
        if regle.type in (TypeRegle.TOTALITE, TypeRegle.PLAFOND_CA, TypeRegle.PLAFOND_EBE):
            assert regle.comptes, regle.id


def test_version_du_referentiel_est_une_empreinte(ref):
    assert len(ref.version) == 12


# ------------------------------------------------------------------ refus des fichiers mal formés
def copie_modifiee(tmp_path, fichier, avant, apres) -> ReferentielYaml:
    shutil.copytree(RACINE / "2026", tmp_path / "2026")
    chemin = tmp_path / "2026" / fichier
    texte = chemin.read_text(encoding="utf-8")
    assert avant in texte
    chemin.write_text(texte.replace(avant, apres, 1), encoding="utf-8")
    return ReferentielYaml(tmp_path)


def test_faute_de_frappe_dans_un_type_est_refusee(tmp_path):
    source = copie_modifiee(tmp_path, "retraitements.yaml", "type: totalite", "type: totalitee")
    with pytest.raises(ReferentielInvalide, match="retraitements.yaml"):
        source.charger(2026)


def test_cle_inconnue_est_refusee(tmp_path):
    source = copie_modifiee(tmp_path, "parametres.yaml", "fraction: 0.25", "fractoin: 0.25")
    with pytest.raises(ReferentielInvalide, match="fractoin"):
        source.charger(2026)


def test_regle_sans_article_est_refusee(tmp_path):
    source = copie_modifiee(tmp_path, "retraitements.yaml", 'article: "CGI art. 35"', 'article: ""')
    with pytest.raises(ReferentielInvalide, match="sans article"):
        source.charger(2026)
