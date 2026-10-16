"""Le référentiel fiscal d'un millésime : paramètres, règles de retraitement, leviers.

Ces objets décrivent CE QU'EST une règle. Ils ne savent pas lire un fichier :
c'est le rôle de l'infrastructure (referentiel_yaml.py). Ainsi, changer de
format de stockage ne touche pas au métier.
"""
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum

from .erreurs import ReferentielInvalide


class TypeRegle(Enum):
    TOTALITE = "totalite"              # tout le solde des comptes listés
    PLAFOND_CA = "plafond_ca"          # part au-delà de (taux × CA HT)
    PLAFOND_EBE = "plafond_ebe"        # intérêts nets au-delà de taux × (RAI + intérêts + dotations), art. 25-3
    SAISIE = "saisie"                  # montant saisi par le collaborateur
    PLAFOND_SAISIE = "plafond_saisie"  # montant saisi, réintégré au-delà de (taux × assiette)


class Sens(Enum):
    REINTEGRATION = "reintegration"    # augmente le résultat fiscal
    DEDUCTION = "deduction"            # diminue le résultat fiscal


class Statut(Enum):
    A_VALIDER = "a_valider"
    VALIDE = "valide"


ASSIETTES_PLAFOND_SAISIE = ("chiffre_affaires", "frais_generaux", "benefice_avant")


@dataclass(frozen=True)
class PlanComptable:
    """Préfixes SYSCOHADA utilisés par le moteur pour lire la balance."""
    charges: tuple[str, ...]
    produits: tuple[str, ...]
    impot_sur_resultat: tuple[str, ...]
    chiffre_affaires: tuple[str, ...]
    dotations: tuple[str, ...]
    charges_exploitation: tuple[str, ...]
    achats_stockes: tuple[str, ...]
    amortissements_exploitation: tuple[str, ...]
    provisions_exploitation: tuple[str, ...]

    @property
    def comptes_de_gestion(self) -> tuple[str, ...]:
        return self.charges + self.produits


@dataclass(frozen=True)
class ParametresAcomptes:
    """Art. 51-52 : échéancier et demande de réduction."""
    echeances: tuple[tuple[int, int], ...]   # (mois, jour), ex. (3, 10) pour le 10 mars
    fraction: Decimal                        # part de l'IS N-1 par acompte (1/4)
    delai_demande_jours: int                 # demande au DGI X jours avant l'échéance
    delai_reponse_dgi_jours: int
    tolerance_inexactitude: Decimal          # au-delà : pénalité (art. 52-7)
    penalite_taux: Decimal
    marge_prudence: Decimal                  # choix du cabinet, pas une règle légale
    article: str


@dataclass(frozen=True)
class Parametres:
    millesime: int
    taux_is: dict[str, Decimal]              # catégorie de taux → taux (art. 46)
    libelles_taux: dict[str, str]
    taux_minimum: dict[str, Decimal]         # secteur → taux du minimum de perception (art. 47)
    libelles_secteur: dict[str, str]
    plancher_minimum: Decimal
    comptes_exclus_encaissables: tuple[str, ...]
    redevance_ortb: Decimal
    article_ortb: str
    acomptes: ParametresAcomptes
    depot_declaration: tuple[int, int]       # (mois, jour) de l'année N+1
    duree_report_deficitaire: int
    seuil_especes: Decimal
    taux_timbre_especes: Decimal
    article_especes: str
    taux_directeur_bceao: Decimal | None
    plan: PlanComptable
    alerte_proximite_seuil: Decimal
    mois_minimum_projection: int


@dataclass(frozen=True)
class Categorie:
    id: str
    court: str
    libelle: str
    aide: str


@dataclass(frozen=True)
class RegleRetraitement:
    id: str
    categorie: str
    libelle: str
    type: TypeRegle
    sens: Sens
    article: str
    statut: Statut
    explication: str = ""
    ou_trouver: str = ""
    comptes: tuple[str, ...] = ()
    comptes_produits: tuple[str, ...] = ()
    taux_plafond: Decimal | None = None
    assiette: str | None = None
    coefficient: Decimal | None = None
    plafond_montant: Decimal | None = None

    def __post_init__(self) -> None:
        if not self.article.strip():
            raise ReferentielInvalide(f"règle {self.id} : une règle sans article n'est pas valide")
        lues_en_balance = (TypeRegle.TOTALITE, TypeRegle.PLAFOND_CA, TypeRegle.PLAFOND_EBE)
        if self.type in lues_en_balance and not self.comptes:
            raise ReferentielInvalide(f"règle {self.id} : le type {self.type.value} exige une liste de comptes")
        a_plafond = (TypeRegle.PLAFOND_CA, TypeRegle.PLAFOND_EBE, TypeRegle.PLAFOND_SAISIE)
        if self.type in a_plafond and self.taux_plafond is None:
            raise ReferentielInvalide(f"règle {self.id} : le type {self.type.value} exige un taux_plafond")
        if self.type is TypeRegle.PLAFOND_SAISIE and self.assiette not in ASSIETTES_PLAFOND_SAISIE:
            raise ReferentielInvalide(f"règle {self.id} : assiette attendue parmi {ASSIETTES_PLAFOND_SAISIE}")

    @property
    def est_saisie(self) -> bool:
        """Vrai si le montant vient du collaborateur et non de la balance."""
        return self.type in (TypeRegle.SAISIE, TypeRegle.PLAFOND_SAISIE)


@dataclass(frozen=True)
class Sanction:
    """Coût hors résultat fiscal (ex. droit de timbre sur paiements en espèces)."""
    id: str
    libelle: str
    article: str
    explication: str = ""
    ou_trouver: str = ""


@dataclass(frozen=True)
class Levier:
    id: str
    libelle: str
    article: str
    conditions: tuple[str, ...]
    effet: str
    moment: str
    parametres: dict = field(default_factory=dict)
    pertinence: tuple[str, ...] = ()
    statut: Statut = Statut.A_VALIDER


@dataclass(frozen=True)
class Referentiel:
    millesime: int
    version: str                             # empreinte des fichiers : change si un YAML change
    parametres: Parametres
    categories: tuple[Categorie, ...]
    regles: tuple[RegleRetraitement, ...]
    sanctions: tuple[Sanction, ...]
    leviers: tuple[Levier, ...]
    perimetre: dict

    def __post_init__(self) -> None:
        ids = [r.id for r in self.regles] + [s.id for s in self.sanctions] + [lv.id for lv in self.leviers]
        doublons = {i for i in ids if ids.count(i) > 1}
        if doublons:
            raise ReferentielInvalide(f"identifiants en double : {sorted(doublons)}")
        categories = {c.id for c in self.categories}
        for regle in self.regles:
            if regle.categorie not in categories:
                raise ReferentielInvalide(f"règle {regle.id} : catégorie inconnue « {regle.categorie} »")

    def regle(self, id_regle: str) -> RegleRetraitement:
        return next(r for r in self.regles if r.id == id_regle)

    def levier(self, id_levier: str) -> Levier:
        return next(lv for lv in self.leviers if lv.id == id_levier)
