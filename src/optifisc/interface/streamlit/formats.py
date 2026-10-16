"""Affichage des montants, pourcentages et dates : le SEUL endroit où l'on formate pour l'écran (doc 05, C.1).

Le séparateur de milliers est une espace fine insécable, quelle que soit la langue du navigateur
(le format « localized » de Streamlit dépendrait du poste utilisé).
"""
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal

ESPACE = " "   # espace fine insécable : « 1 234 567 » ne se coupe pas en fin de ligne
MOIS = ("janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre",
        "novembre", "décembre")


def montant(valeur: Decimal | int | None, unite: bool = False) -> str:
    """Decimal("36840000") → « 36 840 000 » (ou « 36 840 000 FCFA »). None → « — »."""
    if valeur is None:
        return "—"
    arrondi = Decimal(valeur).quantize(Decimal(1), rounding=ROUND_HALF_UP)
    texte = f"{arrondi:,.0f}".replace(",", ESPACE).replace("-", "−")
    return f"{texte} FCFA" if unite else texte


def millions(valeur: Decimal | int | None) -> str:
    """36 840 000 → « 36,8 M FCFA » ; sous le million, montant complet."""
    if valeur is None:
        return "—"
    if abs(valeur) >= 1_000_000:
        return f"{Decimal(valeur) / 1_000_000:,.1f}".replace(",", ESPACE).replace(".", ",") + " M FCFA"
    return montant(valeur, unite=True)


def pourcentage(taux: Decimal) -> str:
    """Decimal("0.30") → « 30 % » ; Decimal("0.001") → « 0,1 % »."""
    return f"{(Decimal(taux) * 100).normalize():f}".replace(".", ",") + f"{ESPACE}%"


def jour(valeur: date | datetime | None) -> str:
    return valeur.strftime("%d/%m/%Y") if valeur else "—"


def horodatage(valeur: datetime) -> str:
    return valeur.strftime("%d/%m %H:%M")


def lire_montant(texte: str) -> Decimal | None:
    """Saisie à l'écran → Decimal. Accepte « 1 500 000 », « 1500000 », « 12,5 ». Vide → None.

    Lève ValueError si le texte n'est pas un montant (message affiché sous le champ).
    """
    nettoye = texte.strip().replace(ESPACE, "").replace(" ", "").replace(" ", "").replace("FCFA", "")
    if not nettoye:
        return None
    nettoye = nettoye.replace(",", ".")
    try:
        valeur = Decimal(nettoye)
    except ArithmeticError as exc:
        raise ValueError(f"« {texte} » n'est pas un montant") from exc
    if not valeur.is_finite():
        raise ValueError(f"« {texte} » n'est pas un montant")
    return valeur
