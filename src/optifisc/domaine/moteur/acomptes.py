"""Acomptes d'IS : échéancier (art. 51) et opportunité de réduction ou de dispense (art. 52) — UC08.

Quatre acomptes de 1/4 de l'IS N-1. Si l'IS de l'année sera plus faible, le cabinet peut
demander au DGI, un mois avant une échéance, de réduire les acomptes restants : c'est un
gain de trésorerie. Trop tard, l'excédent devient un crédit d'impôt.
La date du jour est un paramètre (et non date.today()) pour que le calcul soit testable.
"""
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from ..dossier import Dossier
from ..montant import ZERO, arrondir_fcfa, en_pourcentage
from ..referentiel import Referentiel
from ..resultat import ResultatFiscal


@dataclass(frozen=True)
class Echeance:
    date: date
    montant_normal: Decimal
    payee: bool
    date_limite_demande: date            # dernière date pour demander une réduction de cet acompte


@dataclass(frozen=True)
class Recommandation:
    prochaine_echeance: date
    deposer_avant: date
    is_estime_declare: Decimal           # IS estimé + marge de prudence, à indiquer dans la demande
    acompte_normal: Decimal
    acompte_demande: Decimal
    dispense: bool
    tresorerie_preservee: Decimal
    marge: Decimal
    risque: str


@dataclass(frozen=True)
class Echeancier:
    echeances: tuple[Echeance, ...]
    acompte_normal: Decimal
    total_normal: Decimal
    deja_paye: Decimal
    restant_normal: Decimal
    excedent_previsible: Decimal         # acomptes normaux − IS estimé
    recommandation: Recommandation | None
    trop_tard: bool                      # excédent, mais plus aucune demande possible
    credit_impot: Decimal
    solde_sans_demande: Decimal          # IS − acomptes − AIB (négatif = crédit)
    solde_avec_demande: Decimal | None
    aib_imputable: Decimal


def echeancier(dossier: Dossier, resultat: ResultatFiscal, referentiel: Referentiel, aujourd_hui: date,
               marge: Decimal | None = None) -> Echeancier:
    p = referentiel.parametres.acomptes
    marge = p.marge_prudence if marge is None else marge
    hyp = dossier.hypotheses
    unite = arrondir_fcfa(hyp.is_n_moins_1 * p.fraction)
    echeances, paye = [], ZERO
    for mois, jour in p.echeances:
        jour_echeance = date(dossier.exercice, mois, jour)
        payee = jour_echeance <= aujourd_hui
        if payee:
            paye += unite
        echeances.append(Echeance(jour_echeance, unite, payee,
                                  jour_echeance - timedelta(days=p.delai_demande_jours)))
    if hyp.acomptes_payes is not None:
        paye = hyp.acomptes_payes
    total_normal = unite * len(echeances)
    restantes = [e for e in echeances if not e.payee]
    ouvertes = [e for e in restantes if e.date_limite_demande >= aujourd_hui]
    excedent = total_normal - resultat.is_du
    estimation = arrondir_fcfa(resultat.is_du * (1 + marge))

    recommandation, trop_tard, credit = None, False, ZERO
    if excedent > 0 and ouvertes:
        nouveau = arrondir_fcfa(max(ZERO, (estimation - paye) / len(restantes)))
        economie = sum((e.montant_normal for e in restantes), ZERO) - nouveau * len(restantes)
        if economie > 0:
            recommandation = Recommandation(
                prochaine_echeance=ouvertes[0].date, deposer_avant=ouvertes[0].date_limite_demande,
                is_estime_declare=estimation, acompte_normal=unite, acompte_demande=nouveau,
                dispense=nouveau == 0, tresorerie_preservee=economie, marge=marge,
                risque=(f"Si l'IS réel dépasse l'estimation de plus de {en_pourcentage(p.tolerance_inexactitude)}, "
                        f"pénalité de {en_pourcentage(p.penalite_taux)} de l'écart (art. 52-7). Marge de prudence "
                        f"retenue : {en_pourcentage(marge)}."),
            )
    elif excedent > 0:
        trop_tard, credit = True, excedent

    solde_avec = None
    if recommandation:
        solde_avec = resultat.is_du - (paye + recommandation.acompte_demande * len(restantes)) - hyp.aib_imputable
    return Echeancier(
        echeances=tuple(echeances), acompte_normal=unite, total_normal=total_normal, deja_paye=paye,
        restant_normal=sum((e.montant_normal for e in restantes), ZERO), excedent_previsible=excedent,
        recommandation=recommandation, trop_tard=trop_tard, credit_impot=credit,
        solde_sans_demande=resultat.is_du - total_normal - hyp.aib_imputable, solde_avec_demande=solde_avec,
        aib_imputable=hyp.aib_imputable,
    )


def date_depot_declaration(dossier: Dossier, referentiel: Referentiel) -> date:
    """Art. 49 : au plus tard le 30 avril de l'année suivante."""
    mois, jour = referentiel.parametres.depot_declaration
    return date(dossier.exercice + 1, mois, jour)
