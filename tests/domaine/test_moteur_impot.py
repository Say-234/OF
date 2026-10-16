"""J4-J5 — projection, retraitements et calcul de l'IS : cas chiffrés calculés À LA MAIN.

Repris de la V2 (tests/test_moteur.py). Un collaborateur peut vérifier chaque cas sur papier.
"""
from conftest import REF, M, balance, dossier
from optifisc.domaine.moteur.impot import calculer_is
from optifisc.domaine.moteur.projection import facteur_projection, projeter


def ligne(resultat, id_regle):
    return next(li for li in resultat.retraitements if li.id_regle == id_regle)


def codes(resultat):
    return {a.code for a in resultat.alertes}


# ------------------------------------------------------------------ IS : droit commun, taux, minimum
def test_is_droit_commun_30():
    # CA 1 000 M, charges 800 M → RC 200 M ; IS 30 % = 60 M ; minimum 1 % × 1 000 M = 10 M
    r = calculer_is(balance(("701", "Ventes", 0, 1000 * M), ("601", "Achats", 800 * M, 0)), dossier(), REF)
    assert r.resultat_fiscal == 200 * M
    assert r.is_droit_commun == 60 * M and r.minimum_perception == 10 * M
    assert r.is_du == 60 * M and r.regime == "droit commun"


def test_taux_25_industriel():
    r = calculer_is(balance(("701", "Ventes", 0, 100 * M), ("601", "Achats", 60 * M, 0)),
                    dossier(categorie_taux="industriel_ou_enseignement"), REF)
    assert r.is_droit_commun == 10 * M                                  # 40 M × 25 %


def test_minimum_btp_3_pourcent_et_exclusions():
    # produits encaissables = 705 (500 M) ; 781 transferts et 791 reprises exclus (art. 47-2)
    r = calculer_is(balance(("705", "Travaux", 0, 500 * M), ("781", "Transferts", 0, 20 * M),
                            ("791", "Reprises", 0, 10 * M), ("601", "Achats", 510 * M, 0)), dossier("btp"), REF)
    assert r.produits_encaissables == 500 * M
    assert r.minimum_perception == 15 * M                               # 3 % × 500 M
    assert r.is_du == 15 * M and r.au_minimum
    assert "MINIMUM_PERCEPTION" in codes(r)


def test_plancher_250000():
    r = calculer_is(balance(("701", "Ventes", 0, 5 * M), ("601", "Achats", 6 * M, 0)), dossier(), REF)
    assert r.is_du == 250_000                                           # 1 % × 5 M = 50 000 < plancher


def test_redevance_ortb_en_sus():
    r = calculer_is(balance(("701", "Ventes", 0, 1000 * M), ("601", "Achats", 800 * M, 0)), dossier(), REF)
    assert r.redevance_ortb == 4000 and r.impot_total == 60 * M + 4000


def test_seuil_de_bascule():
    # minimum 10 M ÷ 30 % = 33 333 333 : en dessous, réduire le résultat ne réduit pas l'impôt
    r = calculer_is(balance(("701", "Ventes", 0, 1000 * M), ("601", "Achats", 800 * M, 0)), dossier(), REF)
    assert r.seuil_bascule == 33_333_333


# ------------------------------------------------------------------ retraitements lus dans la balance
def test_reintegrations_amendes_is_dons_cadeaux():
    # CA 1 000 M ; amendes 2 M ; IS comptabilisé 5 M ; dons 3 M (plafond 1 ‰ = 1 M) ; cadeaux 4 M (plafond 3 ‰ = 3 M)
    r = calculer_is(balance(("701", "Ventes", 0, 1000 * M), ("601", "Achats", 700 * M, 0),
                            ("647", "Amendes", 2 * M, 0), ("891", "IS", 5 * M, 0), ("6582", "Dons", 3 * M, 0),
                            ("6276", "Cadeaux", 4 * M, 0)), dossier(), REF)
    # RC = 1 000 − 714 = 286 ; réintégrations = 2 + 5 + 2 + 1 = 10
    assert r.resultat_comptable == 286 * M
    assert r.reintegrations == 10 * M
    assert r.resultat_fiscal == 296 * M


def test_interets_30_pourcent_ebe():
    # RAI = 1000 − 900 − 60 = 40 ; intérêts 60 ; dotations 0 → assiette 100 ; plafond 30 ; réintégration 30
    r = calculer_is(balance(("701", "Ventes", 0, 1000 * M), ("601", "Achats", 900 * M, 0),
                            ("671", "Intérêts", 60 * M, 0)), dossier(), REF)
    assert ligne(r, "R05_INTERETS_30_EBE").montant == 30 * M


def test_interets_nets_des_produits_financiers():
    # art. 25-3 : intérêts NETS = 60 − 10 = 50 ; RAI = 1010 − 960 = 50 ; assiette 100 ; plafond 30 → 20
    r = calculer_is(balance(("701", "Ventes", 0, 1000 * M), ("771", "Intérêts reçus", 0, 10 * M),
                            ("601", "Achats", 900 * M, 0), ("671", "Intérêts", 60 * M, 0)), dossier(), REF)
    assert ligne(r, "R05_INTERETS_30_EBE").montant == 20 * M


def test_deficits_imputes_dans_la_limite_du_benefice():
    r = calculer_is(balance(("701", "Ventes", 0, 100 * M), ("601", "Achats", 80 * M, 0)),
                    dossier(deficits_anterieurs=50 * M), REF)
    assert r.deficit_impute == 20 * M and r.resultat_fiscal == 0


# ------------------------------------------------------------------ retraitements saisis
def test_saisie_manuelle_tvm():
    r = calculer_is(balance(("701", "Ventes", 0, 100 * M), ("601", "Achats", 80 * M, 0)),
                    dossier(saisies={"R06_TVM": 1 * M}), REF)
    assert r.resultat_fiscal == 21 * M


def test_frais_siege_10_pourcent_du_benefice_avant_frais():
    # art. 28-2 : RC 250 (frais de 50 déjà en charges) ; bénéfice avant frais = 300 ; plafond 30 → 20
    r = calculer_is(balance(("701", "Ventes", 0, 1000 * M), ("601", "Achats", 700 * M, 0),
                            ("632", "Frais de siège", 50 * M, 0)), dossier(saisies={"R16_FRAIS_SIEGE": 50 * M}), REF)
    assert ligne(r, "R16_FRAIS_SIEGE").montant == 20 * M
    assert r.resultat_fiscal == 270 * M


def test_assistance_technique_10_pourcent_des_frais_generaux():
    # art. 28-3 : charges d'exploitation 750 − achats stockés 400 − amortissements 50 = frais généraux 300
    # plafond 10 % = 30 ; saisi 45 → réintégration 15
    r = calculer_is(balance(("701", "Ventes", 0, 1000 * M), ("601", "Achats", 400 * M, 0),
                            ("632", "Assistance", 100 * M, 0), ("661", "Salaires", 200 * M, 0),
                            ("681", "Dotations", 50 * M, 0)),
                    dossier(saisies={"R17_ASSISTANCE_TECHNIQUE": 45 * M}), REF)
    assert ligne(r, "R17_ASSISTANCE_TECHNIQUE").montant == 15 * M


def test_redevances_etranger_5_pourcent_du_ca():
    # art. 27-2 : plafond 5 % × 1 000 = 50 ; saisi 80 → réintégration 30
    r = calculer_is(balance(("701", "Ventes", 0, 1000 * M), ("601", "Achats", 700 * M, 0)),
                    dossier(saisies={"R18_REDEVANCES_ETRANGER": 80 * M}), REF)
    assert ligne(r, "R18_REDEVANCES_ETRANGER").montant == 30 * M


def test_revenus_mobiliers_deduits_a_70_pourcent():
    # art. 15-2 : quote-part de frais de 30 % → 10 M saisis, 7 M déduits
    r = calculer_is(balance(("701", "Ventes", 0, 100 * M), ("601", "Achats", 50 * M, 0)),
                    dossier(saisies={"D02_REVENUS_MOBILIERS": 10 * M}), REF)
    assert r.deductions == 7 * M and r.resultat_fiscal == 43 * M


def test_dons_etat_limites_a_25_millions():
    # art. 32-2 : 40 M saisis, déduction plafonnée à 25 M
    r = calculer_is(balance(("701", "Ventes", 0, 100 * M), ("601", "Achats", 50 * M, 0)),
                    dossier(saisies={"R12_DONS_ETAT_SUPPLEMENT": 40 * M}), REF)
    assert r.deductions == 25 * M


def test_especes_timbre_hors_resultat():
    # art. 423-4 et 503-1 : 5 M payés en espèces → timbre 1 % = 50 000 ; le résultat fiscal ne change pas
    r = calculer_is(balance(("701", "Ventes", 0, 100 * M), ("601", "Achats", 80 * M, 0)),
                    dossier(saisies={"S01_TIMBRE_ESPECES": 5 * M}), REF)
    assert r.resultat_fiscal == 20 * M
    assert r.hors_resultat[0].montant == 50_000


def test_neant_different_de_non_renseigne():
    r = calculer_is(balance(("701", "Ventes", 0, 100 * M), ("601", "Achats", 80 * M, 0)),
                    dossier(saisies={"R06_TVM": 0}), REF)
    assert ligne(r, "R06_TVM").renseignee                               # 0 saisi = « néant »
    assert not ligne(r, "R11_DEPENSES_SOMPTUAIRES").renseignee          # absent = non renseigné
    assert "R06_TVM" not in r.saisies_manquantes


# ------------------------------------------------------------------ projection en cours d'année
def test_facteur_de_projection():
    assert facteur_projection(dossier(mois_arrete=6).hypotheses) == 2
    assert facteur_projection(dossier(mois_arrete=4).hypotheses) == 3


def test_projection_semestrielle():
    # 6 mois : CA 50, charges 40 → annuel 100 / 80 ; + dotations prévues 5 → RC 15
    d = dossier(mois_arrete=6, ajustements=[("6813", 5 * M)])
    r = calculer_is(balance(("701", "Ventes", 0, 50 * M), ("601", "Achats", 40 * M, 0)), d, REF)
    assert r.chiffre_affaires == 100 * M
    assert r.resultat_comptable == 15 * M


def test_bilan_non_projete_et_is_comptabilise_non_extrapole():
    d = dossier(mois_arrete=6)
    bp = projeter(balance(("521", "Banque", 10 * M, 0), ("891", "IS", 3 * M, 0), ("701", "Ventes", 0, 50 * M)),
                  d.hypotheses, REF.parametres.plan)
    assert bp.total_charges(("5",)) == 0                                # le bilan disparaît de la projection
    assert bp.total_charges(("89",)) == 3 * M                           # l'IS comptabilisé n'est pas doublé
    assert bp.total_produits(("70",)) == 100 * M


def test_alerte_projection_fragile_en_debut_d_annee():
    r = calculer_is(balance(("701", "Ventes", 0, 20 * M), ("601", "Achats", 10 * M, 0)), dossier(mois_arrete=2), REF)
    assert "PROJECTION_FRAGILE" in codes(r)


def test_piste_d_audit_relie_chaque_montant_a_un_article():
    r = calculer_is(balance(("701", "Ventes", 0, 1000 * M), ("601", "Achats", 700 * M, 0),
                            ("647", "Amendes", 2 * M, 0)), dossier(), REF)
    assert all(ligne_audit.article for ligne_audit in r.audit)
    assert {a.reference for a in r.audit} >= {"RC", "R02_AMENDES_PENALITES", "ART46", "ART47", "IS", "ORTB"}

