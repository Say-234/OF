"""J1 — montants (Decimal) et balance (totaux par préfixe, contrôles)."""
from decimal import Decimal

import pytest

from conftest import M, balance
from optifisc.domaine.balance import LigneBalance, Niveau, RapportLecture, controler
from optifisc.domaine.erreurs import DonneeInvalide
from optifisc.domaine.montant import arrondir_fcfa, vers_decimal


# ------------------------------------------------------------------ montants
def test_decimal_est_exact_contrairement_au_float():
    assert 0.1 + 0.2 != 0.3
    assert vers_decimal("0.1") + vers_decimal("0.2") == Decimal("0.3")


@pytest.mark.parametrize("entree, attendu", [("1500000", Decimal(1500000)), (42, Decimal(42)),
                                             (Decimal("0.30"), Decimal("0.30")), (" 12.5 ", Decimal("12.5"))])
def test_vers_decimal_accepte_chaine_entier_decimal(entree, attendu):
    assert vers_decimal(entree) == attendu


@pytest.mark.parametrize("entree", [0.1, True, "douze", None])
def test_vers_decimal_refuse_float_booleen_et_texte(entree):
    with pytest.raises(DonneeInvalide):
        vers_decimal(entree)


@pytest.mark.parametrize("entree, attendu", [("1234.5", 1235), ("1234.49", 1234), ("-0.5", -1), ("7", 7)])
def test_arrondi_au_franc_demi_au_dessus(entree, attendu):
    assert arrondir_fcfa(Decimal(entree)) == Decimal(attendu)


# ------------------------------------------------------------------ balance
def test_solde_est_debit_moins_credit():
    assert LigneBalance("601", "Achats", Decimal(80), Decimal(0)).solde == 80
    assert LigneBalance("701", "Ventes", Decimal(0), Decimal(100)).solde == -100


def test_ligne_refuse_compte_non_numerique_et_float():
    with pytest.raises(DonneeInvalide):
        LigneBalance("TOTAL", "Total", Decimal(1), Decimal(0))
    with pytest.raises(DonneeInvalide):
        LigneBalance("601", "Achats", 1.0, Decimal(0))


def test_totaux_par_prefixe_avec_exclusion():
    b = balance(("6471", "Pénalités", 2 * M, 0), ("6478", "Amendes", 1 * M, 0), ("601", "Achats", 50 * M, 0),
                ("701", "Ventes", 0, 100 * M), ("781", "Transferts", 0, 5 * M))
    assert b.total_charges(("647",)) == 3 * M                         # « 647 » couvre 6471 et 6478
    assert b.total_produits(("7",)) == 105 * M                        # produits en positif
    assert b.total_produits(("7",), exclure=("78",)) == 100 * M


# ------------------------------------------------------------------ contrôles
def niveaux(controles):
    return {c.niveau for c in controles}


def test_controle_balance_desequilibree_et_montant_illisible():
    b = balance(("521", "Banque", 100, 0), ("601", "Achats", 50, 0), ("701", "Ventes", 0, 0))
    rapport = RapportLecture(fichier="b.xlsx", valeurs_illisibles=("ligne 4 : « douze »",))
    assert {Niveau.ERREUR, Niveau.ATTENTION} <= niveaux(controler(b, rapport))


def test_controle_balance_de_gestion_seule_est_signalee_sans_erreur():
    b = balance(("601", "Achats", 50, 0), ("701", "Ventes", 0, 100))
    assert niveaux(controler(b)) == {Niveau.INFO}
