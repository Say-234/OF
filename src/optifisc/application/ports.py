"""Ports : ce dont la couche Application a besoin, sans dire comment c'est fait.

Un Protocol décrit une forme (des méthodes et leurs signatures). N'importe quelle
classe qui possède ces méthodes convient, sans héritage : l'adaptateur SQLite,
un faux dépôt en mémoire dans les tests, etc. (doc 01, B.5).
"""
from datetime import date, datetime
from typing import Protocol

from optifisc.domaine.balance import Balance, RapportLecture
from optifisc.domaine.dossier import Dossier
from optifisc.domaine.journal import EvenementAudit
from optifisc.domaine.referentiel import Referentiel
from optifisc.domaine.scenario import Scenario
from optifisc.domaine.utilisateur import Utilisateur


# ------------------------------------------------------------------ données de référence et fichiers
class SourceReferentiel(Protocol):
    def charger(self, millesime: int) -> Referentiel: ...


class LecteurBalance(Protocol):
    def lire(self, contenu: bytes, nom_fichier: str) -> tuple[Balance, RapportLecture]: ...


class Horloge(Protocol):
    def aujourd_hui(self) -> date: ...

    def maintenant(self) -> datetime: ...


# ------------------------------------------------------------------ dépôts (persistance)
class DepotDossiers(Protocol):
    def enregistrer(self, dossier: Dossier) -> None: ...

    def charger(self, id_dossier: str) -> Dossier | None: ...

    def lister(self) -> list[Dossier]: ...


class DepotBalances(Protocol):
    def enregistrer(self, dossier_id: str, balance: Balance, rapport: RapportLecture, date_arrete: date,
                    par: str, quand: datetime) -> None: ...

    def derniere(self, dossier_id: str) -> tuple[Balance, RapportLecture, date] | None: ...


class DepotDonneesDossier(Protocol):
    """Données annexes d'un dossier rangées par clé : décision sur les acomptes, résultat figé, propositions…"""

    def sauver(self, dossier_id: str, cle: str, valeur: dict) -> None: ...

    def lire(self, dossier_id: str, cle: str) -> dict | None: ...


class DepotPreferences(Protocol):
    """Préférences par utilisateur (progression du tutoriel…)."""

    def sauver(self, email: str, cle: str, valeur: dict) -> None: ...

    def lire(self, email: str, cle: str) -> dict | None: ...


class DepotScenarios(Protocol):
    def enregistrer(self, scenario: Scenario) -> None: ...

    def lister(self, dossier_id: str) -> list[Scenario]: ...

    def supprimer(self, scenario_id: str) -> None: ...


class DepotValidationsRegles(Protocol):
    def valider(self, id_regle: str, version: str, par: str, cas: str, commentaire: str, quand: datetime) -> None: ...

    def annuler(self, id_regle: str) -> None: ...

    def lister(self) -> dict[str, dict]: ...


class DepotUtilisateurs(Protocol):
    def ajouter(self, utilisateur: Utilisateur, sel: str, empreinte: str) -> None: ...

    def charger(self, email: str) -> Utilisateur | None: ...

    def lister(self) -> list[Utilisateur]: ...

    def modifier(self, utilisateur: Utilisateur) -> None: ...

    def identifiants(self, email: str) -> tuple[str, str] | None: ...

    def changer_mot_de_passe(self, email: str, sel: str, empreinte: str, doit_changer: bool) -> None: ...

    def etat_connexion(self, email: str) -> tuple[int, datetime | None]: ...

    def noter_connexion(self, email: str, echecs: int, bloque_jusqu: datetime | None,
                        derniere: datetime | None) -> None: ...


class Journal(Protocol):
    """Piste d'audit en ajout seul : pas de méthode de modification ni de suppression."""

    def ajouter(self, evenement: EvenementAudit) -> None: ...

    def lister(self, dossier_id: str | None = None, limite: int = 50) -> list[EvenementAudit]: ...


# ------------------------------------------------------------------ sécurité
class ServiceMotsDePasse(Protocol):
    def hacher(self, mot_de_passe: str) -> tuple[str, str]: ...          # (sel, empreinte)

    def verifier(self, mot_de_passe: str, sel: str, empreinte: str) -> bool: ...

    def generer(self) -> str: ...

    def probleme(self, mot_de_passe: str) -> str | None: ...             # None si le mot de passe est acceptable


# ------------------------------------------------------------------ livrables
class GenerateurLivrables(Protocol):
    """Met en forme les données rassemblées par application/livrables.py (DonneesLivrables → [Livrable])."""

    def generer(self, donnees) -> list: ...


# ------------------------------------------------------------------ IA (doc 01, A.3 et A.4)
class RechercheArticles(Protocol):
    def rechercher(self, question: str, k: int = 5) -> list: ...          # [ArticleTrouve]

    def article(self, numero: str, source: str = "CGI 2026"): ...          # Article | None

    def similarite(self, texte: str, numero: str) -> float: ...


class FournisseurIA(Protocol):
    """Modèle de langage (« Système 2 »). Ne reçoit JAMAIS de données identifiantes (pare-feu, doc 01 A.3)."""
    disponible: bool
    nom: str
    confidentiel: bool                    # True si hébergé dans un environnement confidentiel (ex. Ollama local)

    def discuter(self, messages: list[dict]) -> str: ...


class ModeleDecision(Protocol):
    """« Système 1 » : pré-tri des leviers et jugement des propositions (doc 01, A.4).
    Implémenté par application/agent/juge.py (JugeDeterministe) ; Jev ou Laya pourraient le remplacer."""

    def pre_trier(self, profil) -> list: ...

    def juger(self, article: str, justification: str, levier_bloquant: bool | None) -> tuple: ...
