"""Profil pseudonymisé : la SEULE vue du dossier que l'agent reçoit (doc 01, A.3, niveau « pseudonymisé »).

Ni raison sociale, ni IFU, ni libellé de compte : uniquement le secteur, le taux et des agrégats
arrondis au million. Un test vérifie qu'aucune donnée identifiante n'en sort.
"""
from decimal import ROUND_HALF_UP, Decimal

from optifisc.domaine.dossier import Dossier
from optifisc.domaine.moteur.acomptes import Echeancier
from optifisc.domaine.moteur.leviers import dons_deja_comptabilises, marge_dons
from optifisc.domaine.proposition import ProfilPseudonymise
from optifisc.domaine.referentiel import Referentiel
from optifisc.domaine.resultat import ResultatFiscal


def millions(montant: Decimal) -> int:
    return int((Decimal(montant) / 1_000_000).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def construire_profil_pseudonymise(dossier: Dossier, resultat: ResultatFiscal, echeancier: Echeancier,
                                   referentiel: Referentiel) -> ProfilPseudonymise:
    deja_dons = dons_deja_comptabilises(referentiel, resultat.balance_projetee)
    return ProfilPseudonymise(
        secteur=dossier.secteur.value,
        categorie_taux=dossier.categorie_taux.value,
        mois_arrete=dossier.hypotheses.mois_arrete,
        chiffre_affaires_millions=millions(resultat.chiffre_affaires),
        resultat_comptable_millions=millions(resultat.resultat_comptable),
        resultat_fiscal_millions=millions(resultat.resultat_fiscal),
        reintegrations_millions=millions(resultat.reintegrations),
        deductions_millions=millions(resultat.deductions),
        au_minimum_de_perception=resultat.au_minimum,
        ecart_au_seuil_millions=millions(resultat.resultat_fiscal - resultat.seuil_bascule),
        excedent_acomptes_millions=millions(max(echeancier.excedent_previsible, Decimal(0))),
        dons_marge_millions=millions(marge_dons(referentiel, deja_dons, resultat.chiffre_affaires)),
    )
