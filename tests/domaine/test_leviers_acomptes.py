"""J6 — leviers avant clôture (art. 32, 39, 40, 41, 20) et acomptes (art. 51-52). Cas repris de la V2."""
from datetime import date
from decimal import Decimal

from conftest import REF, M, balance, calculer_demo, dossier
from optifisc.domaine.moteur import leviers as L
from optifisc.domaine.moteur.acomptes import date_depot_declaration, echeancier
from optifisc.domaine.moteur.impot import calculer_is


def total(effet) -> Decimal:
    return sum(a.montant for a in effet.ajustements)


# ------------------------------------------------------------------ leviers
def test_degressif_art40():
    # 60 M, 5 ans → coefficient 2 ; acquisition en octobre → 3/12 ; dégressif 60 × 40 % × 3/12 = 6 M
    assert total(L.investissement_degressif(REF, Decimal(60 * M), 5, 10)) == 6 * M


def test_degressif_refuse_sous_10_millions():
    e = L.investissement_degressif(REF, Decimal(8 * M), 5, 10)
    assert total(e) == Decimal("0.4") * M                       # linéaire seul : 8 × 20 % × 3/12
    assert any("NON ÉLIGIBLE" in c for c in e.conformite)
    assert not e.decale_l_impot


def test_accelere_art39_premiere_annuite_doublee():
    # 70 M, 7 ans, octobre : linéaire 70/7 × 3/12 = 2,5 M ; doublée = 5 M
    assert total(L.investissement_accelere(REF, Decimal(70 * M), 7, 10)) == 5 * M


def test_accelere_refuse_si_duree_5_ans():
    e = L.investissement_accelere(REF, Decimal(60 * M), 5, 10)    # durée non > 5 ans
    assert total(e) == 3 * M                                     # linéaire seul : 60/5 × 3/12
    assert any("NON ÉLIGIBLE" in c for c in e.conformite)


def test_levier_sans_effet_au_minimum_de_perception():
    b = balance(("705", "Travaux", 0, 500 * M), ("601", "Achats", 480 * M, 0))
    s = L.simuler(b, dossier("btp"), REF, [L.provision(REF, Decimal(5 * M), True, True)])
    assert s.gain_is == 0
    assert "minimum de perception" in s.lecture[0]


def test_levier_gain_droit_commun():
    b = balance(("701", "Ventes", 0, 1000 * M), ("601", "Achats", 800 * M, 0))
    s = L.simuler(b, dossier(), REF, [L.provision(REF, Decimal(10 * M), True, True)])
    assert s.gain_is == 3 * M                                    # 10 M × 30 %


def test_provision_non_justifiee_bloquante_et_ignoree():
    b = balance(("701", "Ventes", 0, 1000 * M), ("601", "Achats", 800 * M, 0))
    e = L.provision(REF, Decimal(10 * M), justifiee=False, au_releve=True)
    assert e.bloquant and L.simuler(b, dossier(), REF, [e]).gain_is == 0


def test_especes_bloquant_et_timbre():
    e = L.charges_anticipees(REF, Decimal(200_000), "Entretien", True)
    assert e.bloquant and any("timbre" in c for c in e.conformite)


def test_marge_de_dons():
    # CA 1 000 M : plafond 1 ‰ = 1 M ; 0,4 M déjà comptabilisés → marge 0,6 M ; + 25 M si dons à l'État
    assert L.marge_dons(REF, Decimal(400_000), Decimal(1000 * M)) == 600_000
    assert L.marge_dons(REF, Decimal(400_000), Decimal(1000 * M), True) == 25_600_000


# ------------------------------------------------------------------ acomptes
def test_demo_btp_dispense_acompte_decembre():
    d, r = calculer_demo("BATI-PLUS SARL")
    assert r.minimum_perception == Decimal("36.84") * M          # 3 % × 1 228 M
    e = echeancier(d, r, REF, date(2026, 9, 23))
    assert e.deja_paye == 39 * M                                  # mars, juin, septembre : 3 × 13 M
    assert e.recommandation.dispense
    assert e.recommandation.deposer_avant == date(2026, 11, 10)   # un mois avant le 10 décembre
    assert e.recommandation.tresorerie_preservee == 13 * M


def test_credit_impot_signale_apres_la_derniere_echeance():
    # 20/12 : les 4 acomptes (52 M) sont versés pour un impôt de 36,84 M → crédit de 15,16 M (art. 51-3)
    d, r = calculer_demo("BATI-PLUS SARL")
    e = echeancier(d, r, REF, date(2026, 12, 20))
    assert e.trop_tard and e.credit_impot == Decimal("15.16") * M


def test_pas_de_reduction_si_acomptes_insuffisants():
    r = calculer_is(balance(("701", "Ventes", 0, 1000 * M), ("601", "Achats", 800 * M, 0)), dossier(), REF)
    e = echeancier(dossier(is_n_moins_1=40 * M), r, REF, date(2026, 5, 1))   # IS 60 M > acomptes 40 M
    assert e.recommandation is None and not e.trop_tard


def test_date_de_depot_de_la_declaration():
    assert date_depot_declaration(dossier(), REF) == date(2027, 4, 30)
