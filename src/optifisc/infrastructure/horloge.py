"""Horloge du système (implémente le port Horloge). Les tests utilisent une horloge figée."""
from datetime import date, datetime


class HorlogeSysteme:
    def aujourd_hui(self) -> date:
        return date.today()

    def maintenant(self) -> datetime:
        return datetime.now()
