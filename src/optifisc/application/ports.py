"""Ports : ce dont la couche Application a besoin, sans dire comment c'est fait.

Un Protocol décrit une forme (des méthodes et leurs signatures). N'importe quelle
classe qui possède ces méthodes convient, sans héritage : l'adaptateur SQLite,
un faux dépôt en mémoire dans les tests, etc. (doc 01, B.5).
"""
from datetime import date
from typing import Protocol

from optifisc.domaine.balance import Balance, RapportLecture
from optifisc.domaine.referentiel import Referentiel


class SourceReferentiel(Protocol):
    def charger(self, millesime: int) -> Referentiel: ...


class LecteurBalance(Protocol):
    def lire(self, contenu: bytes, nom_fichier: str) -> tuple[Balance, RapportLecture]: ...


class Horloge(Protocol):
    def aujourd_hui(self) -> date: ...
