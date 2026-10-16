"""J3 — lecture des balances au format réel des logiciels comptables (tests repris de la V2)."""
from decimal import Decimal
from io import BytesIO
from pathlib import Path

import pytest
from openpyxl import Workbook

from conftest import M
from optifisc.domaine.erreurs import BalanceIllisible
from optifisc.infrastructure.lecteur_balance import LecteurBalanceTableur, nombre

DEMO = Path(__file__).resolve().parents[2] / "referentiel" / "demo"
lecteur = LecteurBalanceTableur()


def xlsx(lignes) -> bytes:
    classeur = Workbook()
    for ligne in lignes:
        classeur.active.append(ligne)
    tampon = BytesIO()
    classeur.save(tampon)
    return tampon.getvalue()


def soldes(balance) -> dict:
    return {ligne.compte: ligne.solde for ligne in balance.lignes}


@pytest.mark.parametrize("brut, attendu", [
    ("1 234 567,89", "1234567.89"), ("1 234 567", "1234567"), ("1.234.567", "1234567"),
    ("1.234.567,50", "1234567.5"), ("1,234,567.50", "1234567.5"), ("(1 500)", "-1500"), ("1500-", "-1500"),
    ("", "0"), ("-", "0"), (2500, "2500"), ("12 000 FCFA", "12000"), (1234.5, "1234.5"),
])
def test_montants_formats_francais_et_anglais(brut, attendu):
    assert nombre(brut) == Decimal(attendu)


def test_montant_illisible_signale():
    assert nombre("douze") is None


def test_demo_8_colonnes_avec_titres_et_totaux():
    balance, rapport = lecteur.lire((DEMO / "balance_BATIPLUS_BTP_30-06-2026.xlsx").read_bytes(), "x.xlsx")
    assert rapport.base == "soldes de fin de période" and rapport.ligne_entete == 6
    assert rapport.lignes_totaux_ignorees >= 7                  # un total par classe + total général
    assert abs(balance.ecart_debit_credit()) < 1                # balance complète équilibrée
    assert balance.total_produits(("70",)) == 612 * M


def test_comptes_de_regroupement_ignores():
    # « 60 » et « 601 » totalisent 601100 : ils ne doivent pas être comptés deux fois
    balance, rapport = lecteur.lire(xlsx([["Compte", "Intitulé", "Débit", "Crédit"], ["60", "Achats", 100, 0],
                                          ["601", "Achats de marchandises", 100, 0],
                                          ["601100", "Achats marchandises", 100, 0],
                                          ["701100", "Ventes", 0, 300]]), "b.xlsx")
    assert [ligne.compte for ligne in balance.lignes] == ["601100", "701100"]
    assert rapport.regroupements_ignores == ("60", "601")


def test_en_tete_groupes_au_dessus_de_la_ligne_compte():
    balance, rapport = lecteur.lire(xlsx([
        ["SOCIETE X"], [None, None, "Soldes à nouveau", None, "Mouvements", None, "Soldes fin", None],
        ["N° compte", "Intitulé", "Débit", "Crédit", "Débit", "Crédit", "Débit", "Crédit"],
        ["601100", "Achats", 0, 0, 120, 20, 100, 0], ["701100", "Ventes", 0, 0, 5, 305, 0, 300]]), "b.xlsx")
    assert rapport.base == "soldes de fin de période"
    assert soldes(balance) == {"601100": 100, "701100": -300}


def test_mouvements_seuls_ajoutes_aux_a_nouveaux():
    balance, _ = lecteur.lire(xlsx([["Compte", "Intitulé", "Solde à nouveau débit", "Solde à nouveau crédit",
                                     "Mouvements débit", "Mouvements crédit"],
                                    ["411000", "Clients", 50, 0, 200, 150],
                                    ["701000", "Ventes", 0, 0, 0, 200]]), "b.xlsx")
    assert soldes(balance) == {"411000": 100, "701000": -200}


def test_csv_excel_francais_encodage_windows():
    balance, rapport = lecteur.lire((DEMO / "formats" / "balance_4_colonnes_excel_fr.csv").read_bytes(), "b.csv")
    assert rapport.encodage == "cp1252"
    assert balance.total_produits(("70",)) > 0


def test_solde_signe_convention_inverse_corrigee():
    balance, rapport = lecteur.lire(xlsx([["Compte", "Libellé", "Solde"], ["601", "Achats", -80],
                                          ["701", "Ventes", 100]]), "b.xlsx")
    assert rapport.signe_inverse
    assert soldes(balance) == {"601": 80, "701": -100}


def test_fichier_sans_colonne_compte():
    with pytest.raises(BalanceIllisible, match="Compte"):
        lecteur.lire(b"a;b\n1;2\n", "x.csv")


def test_fichier_qui_n_est_pas_un_classeur():
    with pytest.raises(BalanceIllisible, match="Excel"):
        lecteur.lire(b"ceci n'est pas un classeur", "x.xlsx")


def test_montant_illisible_compte_pour_zero_et_signale():
    balance, rapport = lecteur.lire(xlsx([["Compte", "Intitulé", "Débit", "Crédit"], ["601", "Achats", 50, 0],
                                          ["701", "Ventes", 0, "douze"]]), "b.xlsx")
    assert soldes(balance)["701"] == 0
    assert len(rapport.valeurs_illisibles) == 1
