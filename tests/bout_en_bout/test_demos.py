"""J5 — JALON DE VÉRITÉ : les dossiers de démonstration redonnent, au franc près, les résultats de la V2.

Les montants attendus ont été obtenus le 16/10/2026 en faisant tourner le moteur de la V2
(OptiFisc_App) et le nouveau moteur sur les mêmes fichiers : les deux sorties étaient identiques.
Hypothèses (referentiel/demo/demos.yaml) : balance au 30/06, même rythme d'activité, dotations à passer.
"""
from decimal import Decimal

import pytest
import yaml

from conftest import DEMO, REF, M
from optifisc.domaine.dossier import Ajustement, Dossier, Hypotheses, Secteur
from optifisc.domaine.moteur.impot import calculer_is
from optifisc.infrastructure.lecteur_balance import LecteurBalanceTableur

DEMOS = {d["raison_sociale"]: d for d in yaml.safe_load((DEMO / "demos.yaml").read_text(encoding="utf-8"))["dossiers"]}

ATTENDUS = {
    "BATI-PLUS SARL": dict(chiffre_affaires=1_224 * M, resultat_comptable=41_600_000, reintegrations=5_504_000,
                           resultat_fiscal=47_104_000, is_droit_commun=14_131_200, minimum_perception=36_840_000,
                           is_du=36_840_000, au_minimum=True),
    "NOVA SERVICES SA": dict(chiffre_affaires=800 * M, resultat_comptable=310_400_000, reintegrations=6_400_000,
                             resultat_fiscal=316_800_000, is_droit_commun=95_040_000, minimum_perception=8_040_000,
                             is_du=95_040_000, au_minimum=False),
}


def calculer_demo(nom: str):
    d = DEMOS[nom]
    balance, _ = LecteurBalanceTableur().lire((DEMO / d["fichier"]).read_bytes(), d["fichier"])
    hypotheses = Hypotheses(mois_arrete=6, is_n_moins_1=Decimal(d["is_n_moins_1"]), aib_imputable=Decimal(d["aib"]),
                            deficits_anterieurs=Decimal(d["deficits"]),
                            ajustements=(Ajustement("6813", "Dotations 2026 à passer",
                                                    Decimal(d["dotations_a_passer"])),))
    dossier = Dossier(id=nom, raison_sociale=nom, secteur=Secteur(d["secteur"]), demonstration=True,
                      hypotheses=hypotheses)
    return dossier, calculer_is(balance, dossier, REF)


@pytest.mark.parametrize("nom", list(ATTENDUS))
def test_demo_identique_a_la_v2_au_franc_pres(nom):
    _, r = calculer_demo(nom)
    for champ, attendu in ATTENDUS[nom].items():
        assert getattr(r, champ) == attendu, champ


@pytest.mark.parametrize("nom", list(ATTENDUS))
def test_tableau_de_passage_tombe_juste(nom):
    _, r = calculer_demo(nom)
    assert r.resultat_comptable + r.reintegrations - r.deductions - r.deficit_impute == r.resultat_fiscal
