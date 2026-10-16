"""Regroupe les ports dont les cas d'usage ont besoin. composition.py le remplit avec les vrais adaptateurs ;
les tests le remplissent avec une base temporaire et une horloge figée."""
from dataclasses import dataclass

from optifisc.domaine.journal import EvenementAudit
from optifisc.domaine.referentiel import Referentiel
from optifisc.domaine.utilisateur import Utilisateur

from .ports import (
    DepotBalances,
    DepotDonneesDossier,
    DepotDossiers,
    DepotScenarios,
    DepotValidationsRegles,
    GenerateurLivrables,
    Horloge,
    Journal,
    LecteurBalance,
)


@dataclass
class Dependances:
    referentiel: Referentiel
    dossiers: DepotDossiers
    balances: DepotBalances
    donnees: DepotDonneesDossier
    scenarios: DepotScenarios
    validations: DepotValidationsRegles
    journal: Journal
    lecteur_balance: LecteurBalance
    horloge: Horloge
    generateur_livrables: GenerateurLivrables | None = None

    def tracer(self, utilisateur: Utilisateur | None, action: str, detail: str = "", dossier_id: str = "") -> None:
        self.journal.ajouter(EvenementAudit(
            quand=self.horloge.maintenant(), utilisateur=utilisateur.email if utilisateur else "",
            role=utilisateur.role.value if utilisateur else "systeme", action=action, detail=detail,
            dossier_id=dossier_id, version_referentiel=self.referentiel.version))
