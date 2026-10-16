"""Projection de la balance à date vers le 31/12 (UC06).

montant annuel = réalisé + réalisé ÷ mois écoulés × mois restants × coefficient d'activité
                = réalisé × facteur

Seuls les comptes de gestion (classes 6, 7, 8) sont projetés : le bilan ne sert qu'aux contrôles.
L'IS déjà comptabilisé (89) n'est pas extrapolé. Les ajustements de fin d'année (dotations
non encore passées, charges connues…) sont ajoutés tels quels.
"""
from decimal import Decimal

from ..balance import Balance, LigneBalance
from ..dossier import Hypotheses
from ..montant import ZERO
from ..referentiel import PlanComptable


def facteur_projection(hypotheses: Hypotheses) -> Decimal:
    """Ex. balance au 30 juin (6 mois), même rythme : 1 + 6/6 × 1 = 2."""
    mois = Decimal(hypotheses.mois_arrete)
    return 1 + (12 - mois) / mois * hypotheses.coef_activite


def projeter(balance: Balance, hypotheses: Hypotheses, plan: PlanComptable) -> Balance:
    facteur = facteur_projection(hypotheses)
    lignes = []
    for ligne in balance.filtrer(plan.comptes_de_gestion):
        if ligne.commence_par(plan.impot_sur_resultat):
            lignes.append(ligne)                               # l'IS comptabilisé n'est pas extrapolé
        else:
            lignes.append(LigneBalance(ligne.compte, ligne.libelle, ligne.debit * facteur, ligne.credit * facteur))
    for aj in hypotheses.ajustements:
        if aj.montant > 0:
            lignes.append(LigneBalance(aj.compte, aj.libelle, aj.montant, ZERO))
        elif aj.montant < 0:
            lignes.append(LigneBalance(aj.compte, aj.libelle, ZERO, -aj.montant))
    return Balance(tuple(lignes))
