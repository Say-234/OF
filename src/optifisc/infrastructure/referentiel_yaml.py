"""Lecture et validation du référentiel YAML (implémente le port SourceReferentiel).

Deux étapes :
1. lire le YAML en transformant chaque nombre décimal en Decimal EXACT
   (le YAML standard produirait un float : 0.30 → 0.29999…) ;
2. valider la forme avec pydantic (champ manquant, faute de frappe, type faux)
   puis construire les objets du domaine.
Toute erreur devient une ReferentielInvalide avec un message lisible.
"""
import hashlib
from decimal import Decimal
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError

from optifisc.domaine.erreurs import ReferentielInvalide
from optifisc.domaine.referentiel import (
    Categorie,
    Levier,
    Parametres,
    ParametresAcomptes,
    PlanComptable,
    Referentiel,
    RegleRetraitement,
    Sanction,
    Sens,
    Statut,
    TypeRegle,
)

FICHIERS = ("parametres.yaml", "retraitements.yaml", "leviers.yaml", "perimetre.yaml")


# ------------------------------------------------------------------ lecture YAML exacte
class _ChargeurDecimal(yaml.SafeLoader):
    """SafeLoader qui lit les nombres à virgule en Decimal au lieu de float."""


def _construire_decimal(chargeur, noeud):
    return Decimal(chargeur.construct_scalar(noeud))


_ChargeurDecimal.add_constructor("tag:yaml.org,2002:float", _construire_decimal)


def lire_yaml(chemin: Path) -> dict:
    try:
        with open(chemin, encoding="utf-8") as f:
            return yaml.load(f, Loader=_ChargeurDecimal)
    except FileNotFoundError as exc:
        raise ReferentielInvalide(f"fichier du référentiel introuvable : {chemin}") from exc
    except yaml.YAMLError as exc:
        raise ReferentielInvalide(f"{chemin.name} : YAML mal formé ({exc})") from exc


# ------------------------------------------------------------------ schéma (forme attendue des fichiers)
class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")   # une clé inconnue (faute de frappe) est refusée


class _TauxIS(_Strict):
    droit_commun: Decimal
    industriel_ou_enseignement: Decimal
    libelles: dict[str, str]
    article: str
    valide_par: str = ""


class _Minimum(_Strict):
    taux_par_secteur: dict[str, Decimal]
    libelles_secteur: dict[str, str]
    plancher_absolu: Decimal
    comptes_exclus_produits_encaissables: dict[str, str]
    article: str
    valide_par: str = ""


class _Ortb(_Strict):
    montant: Decimal
    article: str
    valide_par: str = ""


class _Reduction(_Strict):
    delai_depot_jours_avant_echeance: int
    delai_reponse_dgi_jours: int
    tolerance_inexactitude: Decimal
    penalite_taux: Decimal
    article: str
    marge_prudence: Decimal


class _Acomptes(_Strict):
    echeances: list[str]
    fraction: Decimal
    article: str
    reduction: _Reduction
    valide_par: str = ""


class _ReportDeficitaire(_Strict):
    duree_exercices: int
    article: str


class _ImpotSocietes(_Strict):
    taux: _TauxIS
    minimum_perception: _Minimum
    redevance_ortb: _Ortb
    acomptes: _Acomptes
    depot_declaration: str
    report_deficitaire: _ReportDeficitaire


class _Especes(_Strict):
    seuil: Decimal
    taux_timbre: Decimal
    article: str
    valide_par: str = ""


class _InteretsAssocies(_Strict):
    taux_directeur_bceao: Decimal | None
    majoration: Decimal
    article: str


class _Plan(_Strict):
    charges: list[str]
    produits: list[str]
    impot_sur_resultat: list[str]
    chiffre_affaires: list[str]
    interets: list[str]
    produits_interets: list[str]
    dotations: list[str]
    charges_exploitation: list[str]
    achats_stockes: list[str]
    amortissements_exploitation: list[str]
    provisions_exploitation: list[str]


class _Alertes(_Strict):
    proximite_seuil_bascule: Decimal
    mois_minimum_projection: int


class _FichierParametres(_Strict):
    millesime: int
    source: str
    exercice: dict
    impot_societes: _ImpotSocietes
    aib: dict
    paiements_especes: _Especes
    interets_associes: _InteretsAssocies
    plan_comptable: _Plan
    alertes: _Alertes


class _Categorie(_Strict):
    id: str
    court: str
    libelle: str
    aide: str


class _Regle(_Strict):
    id: str
    categorie: str
    libelle: str
    type: TypeRegle
    sens: Sens
    article: str
    statut: Statut
    valide_par: str = ""
    explication: str = ""
    ou_trouver: str = ""
    comptes: list[str] = []
    comptes_produits: list[str] = []
    taux_plafond: Decimal | None = None
    assiette: str | None = None
    coefficient: Decimal | None = None
    plafond_montant: Decimal | None = None


class _Sanction(_Strict):
    id: str
    libelle: str
    type: str
    parametre: str
    article: str
    explication: str = ""
    ou_trouver: str = ""
    statut: Statut
    valide_par: str = ""


class _FichierRetraitements(_Strict):
    categories: list[_Categorie]
    regles: list[_Regle]
    sanctions: list[_Sanction] = []


class _Levier(_Strict):
    id: str
    libelle: str
    article: str
    conditions: list[str]
    effet: str
    moment: str
    parametres: dict = {}
    pertinence: list[str] = []
    statut: Statut


class _FichierLeviers(_Strict):
    leviers: list[_Levier]


# ------------------------------------------------------------------ conversion vers le domaine
def _mois_jour(texte: str) -> tuple[int, int]:
    mois, jour = texte.split("-")
    return int(mois), int(jour)


def _parametres(f: _FichierParametres) -> Parametres:
    isp = f.impot_societes
    red = isp.acomptes.reduction
    return Parametres(
        millesime=f.millesime,
        taux_is={"droit_commun": isp.taux.droit_commun,
                 "industriel_ou_enseignement": isp.taux.industriel_ou_enseignement},
        libelles_taux=isp.taux.libelles,
        taux_minimum=isp.minimum_perception.taux_par_secteur,
        libelles_secteur=isp.minimum_perception.libelles_secteur,
        plancher_minimum=isp.minimum_perception.plancher_absolu,
        comptes_exclus_encaissables=tuple(isp.minimum_perception.comptes_exclus_produits_encaissables),
        redevance_ortb=isp.redevance_ortb.montant,
        article_ortb=isp.redevance_ortb.article,
        acomptes=ParametresAcomptes(
            echeances=tuple(_mois_jour(e) for e in isp.acomptes.echeances),
            fraction=isp.acomptes.fraction,
            delai_demande_jours=red.delai_depot_jours_avant_echeance,
            delai_reponse_dgi_jours=red.delai_reponse_dgi_jours,
            tolerance_inexactitude=red.tolerance_inexactitude,
            penalite_taux=red.penalite_taux,
            marge_prudence=red.marge_prudence,
            article=red.article,
        ),
        depot_declaration=_mois_jour(isp.depot_declaration),
        duree_report_deficitaire=isp.report_deficitaire.duree_exercices,
        seuil_especes=f.paiements_especes.seuil,
        taux_timbre_especes=f.paiements_especes.taux_timbre,
        article_especes=f.paiements_especes.article,
        taux_directeur_bceao=f.interets_associes.taux_directeur_bceao,
        plan=PlanComptable(**{nom: tuple(v) for nom, v in f.plan_comptable.model_dump().items()
                              if nom not in ("interets", "produits_interets")}),
        alerte_proximite_seuil=f.alertes.proximite_seuil_bascule,
        mois_minimum_projection=f.alertes.mois_minimum_projection,
    )


def _regle(r: _Regle) -> RegleRetraitement:
    return RegleRetraitement(
        id=r.id, categorie=r.categorie, libelle=r.libelle, type=r.type, sens=r.sens, article=r.article,
        statut=r.statut, explication=r.explication, ou_trouver=r.ou_trouver, comptes=tuple(r.comptes),
        comptes_produits=tuple(r.comptes_produits), taux_plafond=r.taux_plafond, assiette=r.assiette,
        coefficient=r.coefficient, plafond_montant=r.plafond_montant,
    )


def _levier(lv: _Levier) -> Levier:
    return Levier(id=lv.id, libelle=lv.libelle, article=lv.article, conditions=tuple(lv.conditions),
                  effet=lv.effet, moment=lv.moment, parametres=lv.parametres,
                  pertinence=tuple(lv.pertinence), statut=lv.statut)


def _valider(modele, donnees: dict, nom_fichier: str):
    try:
        return modele.model_validate(donnees)
    except ValidationError as exc:
        erreurs = "; ".join(f"{'.'.join(str(x) for x in e['loc'])} : {e['msg']}" for e in exc.errors()[:5])
        raise ReferentielInvalide(f"{nom_fichier} : {erreurs}") from exc


# ------------------------------------------------------------------ adaptateur
class ReferentielYaml:
    """Charge referentiel/<millésime>/*.yaml. Implémente le port SourceReferentiel."""

    def __init__(self, racine: Path):
        self.racine = Path(racine)

    def charger(self, millesime: int) -> Referentiel:
        dossier = self.racine / str(millesime)
        brut = {nom: lire_yaml(dossier / nom) for nom in FICHIERS}
        param = _valider(_FichierParametres, brut["parametres.yaml"], "parametres.yaml")
        retr = _valider(_FichierRetraitements, brut["retraitements.yaml"], "retraitements.yaml")
        lev = _valider(_FichierLeviers, brut["leviers.yaml"], "leviers.yaml")
        if param.millesime != millesime:
            raise ReferentielInvalide(f"parametres.yaml annonce le millésime {param.millesime}, attendu {millesime}")
        return Referentiel(
            millesime=millesime,
            version=self._empreinte(dossier),
            parametres=_parametres(param),
            categories=tuple(Categorie(**c.model_dump()) for c in retr.categories),
            regles=tuple(_regle(r) for r in retr.regles),
            sanctions=tuple(Sanction(id=s.id, libelle=s.libelle, article=s.article, explication=s.explication,
                                     ou_trouver=s.ou_trouver) for s in retr.sanctions),
            leviers=tuple(_levier(lv) for lv in lev.leviers),
            perimetre=brut["perimetre.yaml"],
        )

    @staticmethod
    def _empreinte(dossier: Path) -> str:
        """12 premiers caractères du SHA-256 des fichiers : identifie la version du référentiel."""
        h = hashlib.sha256()
        for nom in FICHIERS:
            h.update((dossier / nom).read_bytes())
        return h.hexdigest()[:12]
