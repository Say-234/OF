"""Piste d'audit des actions : qui a fait quoi, quand, sur quel dossier (doc 02, §5.4).

Le journal n'accepte que des AJOUTS : aucune fonction de modification ni de suppression.
"""
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class EvenementAudit:
    quand: datetime
    utilisateur: str              # e-mail ("" pour le système)
    role: str
    action: str                   # ex. « balance_importee », « dossier_valide », « appel_ia »
    detail: str
    dossier_id: str = ""
    version_referentiel: str = ""
