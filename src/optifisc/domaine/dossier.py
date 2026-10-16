"""Le dossier client : identité fiscale, hypothèses de projection, saisies, état (doc 02 et 03)."""
from dataclasses import dataclass, field, replace
from decimal import Decimal
from enum import Enum

from .erreurs import DonneeInvalide, DossierFige, TransitionInterdite
from .montant import ZERO


class Secteur(Enum):
    """Secteur au sens du minimum de perception (art. 47) : liste fermée, jamais du texte libre."""
    AUTRES = "autres"
    BTP = "btp"
    IMMOBILIER = "immobilier"


class CategorieTaux(Enum):
    """Catégorie de taux d'IS (art. 46)."""
    DROIT_COMMUN = "droit_commun"
    INDUSTRIEL_OU_ENSEIGNEMENT = "industriel_ou_enseignement"


class EtatDossier(Enum):
    BROUILLON = "brouillon"
    EN_PREPARATION = "en_preparation"
    CALCULE = "calcule"
    A_VALIDER = "a_valider"
    VALIDE = "valide"
    LIVRE = "livre"


# Cycle de vie (doc 02, §3) : état actuel → états atteignables
TRANSITIONS = {
    EtatDossier.BROUILLON: {EtatDossier.EN_PREPARATION},
    EtatDossier.EN_PREPARATION: {EtatDossier.CALCULE},
    EtatDossier.CALCULE: {EtatDossier.EN_PREPARATION, EtatDossier.A_VALIDER},
    EtatDossier.A_VALIDER: {EtatDossier.EN_PREPARATION, EtatDossier.VALIDE},
    EtatDossier.VALIDE: {EtatDossier.LIVRE, EtatDossier.EN_PREPARATION},
    EtatDossier.LIVRE: {EtatDossier.EN_PREPARATION},
}
ETATS_FIGES = {EtatDossier.A_VALIDER, EtatDossier.VALIDE, EtatDossier.LIVRE}


@dataclass(frozen=True)
class Ajustement:
    """Écriture prévisionnelle de fin d'année (dotation non encore passée, charge connue…).

    montant > 0 : charge supplémentaire ; montant < 0 : produit supplémentaire.
    """
    compte: str
    libelle: str
    montant: Decimal


@dataclass(frozen=True)
class Hypotheses:
    """Ce que suppose le collaborateur (UC06), distinct de ce que dit la balance."""
    mois_arrete: int = 12                       # balance arrêtée à la fin de ce mois
    coef_activite: Decimal = Decimal("1")       # 1 = le reste de l'année ressemble au passé
    ajustements: tuple[Ajustement, ...] = ()
    is_n_moins_1: Decimal = ZERO                # base des acomptes (art. 51)
    aib_imputable: Decimal = ZERO               # art. 133-4
    deficits_anterieurs: Decimal = ZERO         # art. 43
    acomptes_payes: Decimal | None = None       # None : déduits de l'échéancier

    def __post_init__(self) -> None:
        if not 1 <= self.mois_arrete <= 12:
            raise DonneeInvalide("le mois d'arrêté doit être compris entre 1 et 12")
        if self.coef_activite < 0:
            raise DonneeInvalide("le coefficient d'activité ne peut pas être négatif")


@dataclass(frozen=True)
class Dossier:
    id: str
    raison_sociale: str
    secteur: Secteur = Secteur.AUTRES
    categorie_taux: CategorieTaux = CategorieTaux.DROIT_COMMUN
    exercice: int = 2026
    demonstration: bool = False                 # dossier fictif : OpenRouter autorisé par défaut (doc 01, A.3)
    responsable: str = ""                       # e-mail du collaborateur attribué
    etat: EtatDossier = EtatDossier.BROUILLON
    hypotheses: Hypotheses = field(default_factory=Hypotheses)
    # Saisies des règles « à saisie » : id de règle → montant. 0 = « néant » ; absent = non renseigné.
    saisies: dict[str, Decimal] = field(default_factory=dict)

    @property
    def est_fige(self) -> bool:
        return self.etat in ETATS_FIGES

    def vers(self, nouvel_etat: EtatDossier) -> "Dossier":
        """Renvoie le dossier dans son nouvel état, si le cycle de vie le permet."""
        if nouvel_etat not in TRANSITIONS[self.etat]:
            raise TransitionInterdite(f"passage de « {self.etat.value} » à « {nouvel_etat.value} » non permis")
        return replace(self, etat=nouvel_etat)

    def verifier_modifiable(self) -> None:
        if self.est_fige:
            raise DossierFige(f"Dossier « {self.etat.value.replace('_', ' ')} » : il ne peut plus être modifié.")

    def modifie(self, **changements) -> "Dossier":
        """Modifie des données. Un dossier calculé repasse « en préparation » (son calcul n'est plus à jour)."""
        self.verifier_modifiable()
        nouveau = replace(self, **changements)
        if nouveau.etat is EtatDossier.CALCULE:
            nouveau = replace(nouveau, etat=EtatDossier.EN_PREPARATION)
        return nouveau
