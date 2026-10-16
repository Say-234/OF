"""Scénario d'optimisation : un ensemble de leviers paramétrés, enregistré pour un dossier (UC03)."""
from dataclasses import dataclass, field
from decimal import Decimal

from .montant import ZERO

NOMBRE_MAXIMUM_DE_SCENARIOS = 3   # par dossier (UC03, variante V2)


@dataclass(frozen=True)
class LevierChoisi:
    """Un levier et ses paramètres tels que saisis (montant, durée, mois, cases de conformité…)."""
    id_levier: str
    parametres: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Scenario:
    id: str
    dossier_id: str
    nom: str                                      # « A », « B », « C »
    leviers: tuple[LevierChoisi, ...]
    gain_is: Decimal = ZERO
    retenu: bool = False
