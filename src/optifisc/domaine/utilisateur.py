"""Utilisateurs et rôles (doc 02)."""
from dataclasses import dataclass
from enum import Enum


class Role(Enum):
    COLLABORATEUR = "collaborateur"
    EXPERT = "expert"
    ADMIN = "admin"


LIBELLES_ROLE = {Role.COLLABORATEUR: "Collaborateur", Role.EXPERT: "Expert-comptable", Role.ADMIN: "Administrateur"}


@dataclass(frozen=True)
class Utilisateur:
    email: str
    nom: str
    role: Role
    actif: bool = True
    doit_changer_mot_de_passe: bool = False

    @property
    def libelle_role(self) -> str:
        return LIBELLES_ROLE[self.role]
