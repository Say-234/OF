"""Assemblage de l'application : le SEUL endroit qui connaît toutes les couches (doc 01, B.2).

Il crée les adaptateurs (SQLite, YAML, lecteur de balance, générateur de livrables, IA)
et les donne aux cas d'usage. Pour tester, on appelle construire() avec une base
temporaire et une horloge figée : aucun autre fichier ne change.
"""
import os
from dataclasses import dataclass
from pathlib import Path

from optifisc.application.balance import ServiceBalance
from optifisc.application.calcul import ServiceCalcul
from optifisc.application.comptes import ServiceComptes
from optifisc.application.dependances import Dependances
from optifisc.application.dossiers import ServiceDossiers
from optifisc.application.livrables import ServiceLivrables
from optifisc.application.scenarios import ServiceScenarios
from optifisc.application.validation import ServiceValidation
from optifisc.infrastructure.horloge import HorlogeSysteme
from optifisc.infrastructure.lecteur_balance import LecteurBalanceTableur
from optifisc.infrastructure.livrables.generateur import GenerateurOffice
from optifisc.infrastructure.persistance.connexion import BaseSqlite
from optifisc.infrastructure.persistance.depots import (
    DepotBalancesSqlite,
    DepotDonneesDossierSqlite,
    DepotDossiersSqlite,
    DepotScenariosSqlite,
    DepotUtilisateursSqlite,
    DepotValidationsSqlite,
    JournalSqlite,
)
from optifisc.infrastructure.referentiel_yaml import ReferentielYaml
from optifisc.infrastructure.securite import MotsDePassePbkdf2

RACINE_PROJET = Path(__file__).resolve().parents[2]
MILLESIME = 2026


@dataclass
class Application:
    """Les cas d'usage prêts à l'emploi, tels que l'interface les utilise."""
    dependances: Dependances
    comptes: ServiceComptes
    dossiers: ServiceDossiers
    balance: ServiceBalance
    calcul: ServiceCalcul
    scenarios: ServiceScenarios
    validation: ServiceValidation
    livrables: ServiceLivrables
    mode: str = "cabinet"

    @property
    def referentiel(self):
        return self.dependances.referentiel


def construire(chemin_base: Path | str | None = None, racine_referentiel: Path | None = None,
               horloge=None, mode: str | None = None) -> Application:
    mode = mode or os.environ.get("OPTIFISC_MODE", "cabinet")
    chemin_base = chemin_base or os.environ.get("OPTIFISC_BASE") or RACINE_PROJET / "var" / f"optifisc_{mode}.sqlite"
    racine_referentiel = racine_referentiel or RACINE_PROJET / "referentiel"
    horloge = horloge or HorlogeSysteme()
    base = BaseSqlite(chemin_base)
    dep = Dependances(
        referentiel=ReferentielYaml(racine_referentiel).charger(MILLESIME),
        dossiers=DepotDossiersSqlite(base), balances=DepotBalancesSqlite(base),
        donnees=DepotDonneesDossierSqlite(base), scenarios=DepotScenariosSqlite(base),
        validations=DepotValidationsSqlite(base), journal=JournalSqlite(base),
        lecteur_balance=LecteurBalanceTableur(), horloge=horloge, generateur_livrables=GenerateurOffice(),
    )
    comptes = ServiceComptes(DepotUtilisateursSqlite(base), MotsDePassePbkdf2(), dep.journal, horloge, dep.dossiers)
    return Application(dep, comptes, ServiceDossiers(dep), ServiceBalance(dep), ServiceCalcul(dep),
                       ServiceScenarios(dep), ServiceValidation(dep), ServiceLivrables(dep), mode)
