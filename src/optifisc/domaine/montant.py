"""Montants en FCFA : la seule porte d'entrée et la seule règle d'arrondi (doc 01, A.2).

Pourquoi Decimal : 0.1 + 0.2 vaut 0.30000000000000004 en float, mais exactement
0.3 en Decimal. Un tableau de passage doit tomber juste au franc.
"""
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from .erreurs import DonneeInvalide

ZERO = Decimal("0")
UN_FRANC = Decimal("1")


def vers_decimal(valeur: Decimal | int | str) -> Decimal:
    """Convertit une valeur en Decimal, en refusant les float.

    Un float a déjà perdu sa précision : on exige une chaîne ("0.30") ou un entier.
    Les bibliothèques Excel renvoient des float : c'est le lecteur de balance
    (infrastructure) qui les convertit en chaîne avant d'appeler cette fonction.
    """
    if isinstance(valeur, bool):  # True est un int en Python : on le refuse explicitement
        raise DonneeInvalide("un booléen n'est pas un montant")
    if isinstance(valeur, Decimal):
        return valeur
    if isinstance(valeur, int):
        return Decimal(valeur)
    if isinstance(valeur, str):
        try:
            return Decimal(valeur.strip())
        except InvalidOperation as exc:
            raise DonneeInvalide(f"montant illisible : « {valeur} »") from exc
    if isinstance(valeur, float):
        raise DonneeInvalide(f"montant en float refusé ({valeur!r}) : passer une chaîne, ex. Decimal(\"{valeur}\")")
    raise DonneeInvalide(f"type de montant non pris en charge : {type(valeur).__name__}")


def arrondir_fcfa(montant: Decimal) -> Decimal:
    """Arrondit au franc, 0,5 arrondi au-dessus (arrondi commercial)."""
    return montant.quantize(UN_FRANC, rounding=ROUND_HALF_UP)


# Écriture des montants DANS LA PISTE D'AUDIT (formules en clair). L'affichage à l'écran
# a ses propres fonctions dans interface/streamlit/formats.py.
def en_texte(montant: Decimal) -> str:
    """1500000 → « 1 500 000 FCFA » (arrondi au franc, espace comme séparateur de milliers)."""
    return f"{arrondir_fcfa(montant):,.0f}".replace(",", " ") + " FCFA"


def en_pourcentage(taux: Decimal) -> str:
    """Decimal("0.30") → « 30 % » ; Decimal("0.001") → « 0,1 % »."""
    texte = f"{(taux * 100).normalize():f}".replace(".", ",")
    return f"{texte} %"
