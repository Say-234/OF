"""Passage du résultat comptable au résultat fiscal : application des règles (UC02, art. 15 à 43).

Patron « stratégie » : une petite fonction par TYPE de règle, et un registre
type → fonction. Ajouter un type = écrire une fonction + l'inscrire au registre,
sans toucher au reste. Chaque fonction renvoie (base, montant, détail).
"""
from dataclasses import dataclass
from decimal import Decimal

from ..balance import Balance
from ..dossier import Dossier
from ..montant import ZERO, arrondir_fcfa, en_pourcentage, en_texte
from ..referentiel import PlanComptable, Referentiel, RegleRetraitement, Sens, Statut, TypeRegle
from ..resultat import CoutHorsResultat, LigneRetraitement


@dataclass(frozen=True)
class Contexte:
    """Ce dont les règles ont besoin, calculé une fois sur la balance projetée."""
    balance: Balance
    plan: PlanComptable
    chiffre_affaires: Decimal
    resultat_comptable: Decimal
    resultat_avant_is: Decimal         # résultat comptable + IS comptabilisé (pour l'art. 25-3)


def frais_generaux(balance: Balance, plan: PlanComptable) -> Decimal:
    """Art. 28-3 : charges d'exploitation − achats stockés − amortissements − provisions."""
    return (balance.total_charges(plan.charges_exploitation) - balance.total_charges(plan.achats_stockes)
            - balance.total_charges(plan.amortissements_exploitation)
            - balance.total_charges(plan.provisions_exploitation))


# ------------------------------------------------------------------ une fonction par type de règle
def _totalite(regle, ctx, saisie, cumul):
    base = ctx.balance.total_charges(regle.comptes)
    return base, max(ZERO, base), f"Solde des comptes {', '.join(regle.comptes)}"


def _plafond_ca(regle, ctx, saisie, cumul):
    base = ctx.balance.total_charges(regle.comptes)
    plafond = regle.taux_plafond * ctx.chiffre_affaires
    detail = (f"{en_texte(base)} comptabilisé − plafond {en_pourcentage(regle.taux_plafond)} × CA "
              f"{en_texte(ctx.chiffre_affaires)} = {en_texte(plafond)}")
    return base, max(ZERO, base - plafond), detail


def _plafond_ebe(regle, ctx, saisie, cumul):
    """Art. 25-3 : intérêts NETS au-delà de 30 % de (résultat avant impôt + intérêts nets + dotations)."""
    bruts = ctx.balance.total_charges(regle.comptes)
    recus = ctx.balance.total_produits(regle.comptes_produits)
    base = max(ZERO, bruts - recus)
    dotations = ctx.balance.total_charges(ctx.plan.dotations)
    assiette = ctx.resultat_avant_is + base + dotations
    plafond = max(ZERO, regle.taux_plafond * assiette)
    detail = (f"Intérêts nets {en_texte(base)} (charges {en_texte(bruts)} − produits {en_texte(recus)}) − "
              f"{en_pourcentage(regle.taux_plafond)} × (résultat avant impôt + intérêts nets + dotations = "
              f"{en_texte(assiette)}) = {en_texte(plafond)}")
    return base, max(ZERO, base - plafond), detail


def _saisie(regle, ctx, saisie, cumul):
    base = saisie or ZERO
    montant = base * (regle.coefficient if regle.coefficient is not None else 1)
    detail = "Montant saisi par le collaborateur"
    if regle.coefficient is not None:
        detail += f" × {en_pourcentage(regle.coefficient)}"
    if regle.plafond_montant is not None and montant > regle.plafond_montant:
        montant = regle.plafond_montant
        detail += f", limité à {en_texte(montant)}"
    return base, montant, detail


def _plafond_saisie(regle, ctx, saisie, cumul):
    base = saisie or ZERO
    if base <= 0:
        return base, ZERO, "Néant"
    if regle.assiette == "chiffre_affaires":
        assiette, nom = ctx.chiffre_affaires, "CA HT"
    elif regle.assiette == "frais_generaux":
        assiette, nom = frais_generaux(ctx.balance, ctx.plan), "frais généraux"
    else:  # benefice_avant : bénéfice avant déduction des frais en cause (art. 28-2)
        reintegre, deduit = cumul
        assiette, nom = ctx.resultat_comptable + reintegre - deduit + base, "bénéfice avant ces frais"
    plafond = max(ZERO, regle.taux_plafond * assiette)
    detail = (f"{en_texte(base)} saisi − plafond {en_pourcentage(regle.taux_plafond)} × {nom} "
              f"{en_texte(assiette)} = {en_texte(plafond)}")
    return base, max(ZERO, base - plafond), detail


REGISTRE = {
    TypeRegle.TOTALITE: _totalite,
    TypeRegle.PLAFOND_CA: _plafond_ca,
    TypeRegle.PLAFOND_EBE: _plafond_ebe,
    TypeRegle.SAISIE: _saisie,
    TypeRegle.PLAFOND_SAISIE: _plafond_saisie,
}


# ------------------------------------------------------------------ application de toutes les règles
def _ordre(regle: RegleRetraitement) -> int:
    """Les plafonds calculés sur le bénéfice passent en dernier : ils dépendent des autres retraitements."""
    return 1 if regle.assiette == "benefice_avant" else 0


def appliquer_retraitements(ctx: Contexte, dossier: Dossier, referentiel: Referentiel) -> tuple[LigneRetraitement, ...]:
    lignes = []
    reintegre = deduit = ZERO
    for regle in sorted(referentiel.regles, key=_ordre):
        saisie = dossier.saisies.get(regle.id)
        base, montant, detail = REGISTRE[regle.type](regle, ctx, saisie, (reintegre, deduit))
        montant = arrondir_fcfa(montant)
        if regle.sens is Sens.REINTEGRATION:
            reintegre += montant
        else:
            deduit += montant
        lignes.append(LigneRetraitement(
            id_regle=regle.id, libelle=regle.libelle, categorie=regle.categorie, article=regle.article,
            sens=regle.sens, base=arrondir_fcfa(base), montant=montant, detail=detail,
            depuis_saisie=regle.est_saisie, renseignee=not regle.est_saisie or saisie is not None,
            a_valider=regle.statut is Statut.A_VALIDER,
        ))
    return tuple(lignes)


def couts_hors_resultat(dossier: Dossier, referentiel: Referentiel) -> tuple[CoutHorsResultat, ...]:
    """Sanctions sans effet sur le résultat fiscal (ex. timbre de 1 % sur paiements en espèces, art. 423-4)."""
    p = referentiel.parametres
    couts = []
    for sanction in referentiel.sanctions:
        base = dossier.saisies.get(sanction.id) or ZERO
        if base > 0:
            couts.append(CoutHorsResultat(sanction.id, sanction.libelle, sanction.article, base,
                                          arrondir_fcfa(base * p.taux_timbre_especes)))
    return tuple(couts)
