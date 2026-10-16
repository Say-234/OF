"""Balance générale SYSCOHADA : lignes de comptes et totaux par préfixe.

Convention : solde = débit − crédit. Une charge (classe 6) a un solde positif,
un produit (classe 7) un solde négatif. total_produits() renvoie donc l'opposé
de la somme des soldes, pour obtenir un montant positif.
Les comptes sont comparés par PRÉFIXE : « 647 » couvre 6471, 6478…
"""
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum

from .erreurs import DonneeInvalide
from .montant import ZERO


@dataclass(frozen=True)
class LigneBalance:
    compte: str
    libelle: str
    debit: Decimal
    credit: Decimal

    def __post_init__(self) -> None:
        if not self.compte.isdigit():
            raise DonneeInvalide(f"numéro de compte invalide : « {self.compte} »")
        for nom in ("debit", "credit"):
            if not isinstance(getattr(self, nom), Decimal):
                raise DonneeInvalide(f"compte {self.compte} : le {nom} doit être un Decimal")

    @property
    def solde(self) -> Decimal:
        return self.debit - self.credit

    def commence_par(self, prefixes: tuple[str, ...]) -> bool:
        return self.compte.startswith(prefixes)


@dataclass(frozen=True)
class Balance:
    lignes: tuple[LigneBalance, ...]

    def filtrer(self, prefixes, exclure=()) -> tuple[LigneBalance, ...]:
        """Lignes dont le compte commence par un des préfixes, sauf les préfixes exclus."""
        prefixes, exclure = tuple(prefixes), tuple(exclure)
        return tuple(
            ligne for ligne in self.lignes
            if ligne.commence_par(prefixes) and not (exclure and ligne.commence_par(exclure))
        )

    def total_charges(self, prefixes, exclure=()) -> Decimal:
        return sum((ligne.solde for ligne in self.filtrer(prefixes, exclure)), ZERO)

    def total_produits(self, prefixes, exclure=()) -> Decimal:
        return -sum((ligne.solde for ligne in self.filtrer(prefixes, exclure)), ZERO)

    def classes_presentes(self) -> set[str]:
        return {ligne.compte[0] for ligne in self.lignes}

    def ecart_debit_credit(self) -> Decimal:
        return sum((ligne.solde for ligne in self.lignes), ZERO)


class Niveau(Enum):
    ERREUR = "erreur"
    ATTENTION = "attention"
    INFO = "info"


@dataclass(frozen=True)
class Controle:
    niveau: Niveau
    message: str


@dataclass(frozen=True)
class RapportLecture:
    """Ce que le lecteur a compris du fichier : affiché au collaborateur avant confirmation (UC01)."""
    fichier: str
    feuille: str = ""
    encodage: str = ""
    ligne_entete: int = 0
    base: str = ""                                  # ex. « soldes de fin de période »
    colonnes: dict = field(default_factory=dict)    # rôle → libellé lu dans le fichier
    lignes_totaux_ignorees: int = 0
    regroupements_ignores: tuple[str, ...] = ()
    valeurs_illisibles: tuple[str, ...] = ()
    signe_inverse: bool = False


def controler(balance: Balance, rapport: RapportLecture | None = None) -> list[Controle]:
    """Contrôles de cohérence d'une balance (UC01, étape 5)."""
    controles: list[Controle] = []
    if rapport and rapport.valeurs_illisibles:
        exemples = " ; ".join(rapport.valeurs_illisibles[:5])
        controles.append(Controle(Niveau.ERREUR, f"{len(rapport.valeurs_illisibles)} montant(s) illisible(s), "
                                                 f"comptés pour 0 : {exemples}"))
    if rapport and rapport.signe_inverse:
        controles.append(Controle(Niveau.ATTENTION, "Colonne solde en convention inverse (produits positifs) : "
                                                    "signes corrigés."))
    classes = balance.classes_presentes()
    if classes & set("12345"):
        ecart = balance.ecart_debit_credit()
        if abs(ecart) > 1:
            controles.append(Controle(Niveau.ATTENTION, f"Balance non équilibrée : écart débit − crédit de "
                                                        f"{ecart:.0f} FCFA. Vérifier qu'aucun compte ne manque."))
    else:
        controles.append(Controle(Niveau.INFO, "Balance limitée aux comptes de gestion (classes 6 à 8) : "
                                               "l'équilibre ne peut pas être contrôlé."))
    if "7" not in classes:
        controles.append(Controle(Niveau.ERREUR, "Aucun compte de produits (classe 7) : vérifier le fichier."))
    if "6" not in classes:
        controles.append(Controle(Niveau.ERREUR, "Aucun compte de charges (classe 6) : vérifier le fichier."))
    if "7" in classes and balance.total_produits(("70",)) <= 0:
        controles.append(Controle(Niveau.ATTENTION, "Chiffre d'affaires (comptes 70) nul ou débiteur : "
                                                    "vérifier le sens des colonnes."))
    return controles
