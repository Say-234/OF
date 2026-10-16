"""Résultats du moteur : lignes de retraitement, piste d'audit, alertes, résultat fiscal."""
from dataclasses import dataclass, field
from decimal import Decimal

from .balance import Balance, Niveau
from .referentiel import Sens


@dataclass(frozen=True)
class LigneRetraitement:
    """Application d'une règle de retraitement à un dossier (une ligne de l'écran E08)."""
    id_regle: str
    libelle: str
    categorie: str
    article: str
    sens: Sens
    base: Decimal
    montant: Decimal                  # arrondi au franc
    detail: str                       # formule appliquée, en clair
    depuis_saisie: bool
    renseignee: bool                  # False : règle à saisie sans réponse (bloquant pour la soumission)
    a_valider: bool                   # règle pas encore validée par le cabinet


@dataclass(frozen=True)
class LigneAudit:
    """Une ligne de la piste d'audit : chaque montant est relié à sa règle et à son article."""
    etape: str
    reference: str
    libelle: str
    article: str
    base: Decimal
    montant: Decimal
    detail: str
    categorie: str = ""


@dataclass(frozen=True)
class Alerte:
    code: str
    niveau: Niveau
    message: str


@dataclass(frozen=True)
class CoutHorsResultat:
    """Sanction qui ne change pas le résultat fiscal (ex. timbre sur paiements en espèces)."""
    id: str
    libelle: str
    article: str
    base: Decimal
    montant: Decimal


@dataclass(frozen=True)
class ResultatFiscal:
    balance_projetee: Balance
    chiffre_affaires: Decimal
    resultat_comptable: Decimal
    retraitements: tuple[LigneRetraitement, ...]
    reintegrations: Decimal
    deductions: Decimal
    deficit_impute: Decimal
    resultat_fiscal: Decimal
    taux_is: Decimal
    is_droit_commun: Decimal
    produits_encaissables: Decimal
    taux_minimum: Decimal
    minimum_perception: Decimal
    is_du: Decimal
    au_minimum: bool                  # True : le minimum de perception s'applique
    seuil_bascule: Decimal            # résultat fiscal à partir duquel l'IS de droit commun dépasse le minimum
    redevance_ortb: Decimal
    version_referentiel: str
    audit: tuple[LigneAudit, ...] = ()
    alertes: tuple[Alerte, ...] = ()
    hors_resultat: tuple[CoutHorsResultat, ...] = field(default_factory=tuple)

    @property
    def regime(self) -> str:
        return "minimum de perception" if self.au_minimum else "droit commun"

    @property
    def impot_total(self) -> Decimal:
        """IS dû + redevance ORTB (art. 47-6)."""
        return self.is_du + self.redevance_ortb

    @property
    def saisies_manquantes(self) -> tuple[str, ...]:
        return tuple(r.id_regle for r in self.retraitements if not r.renseignee)
