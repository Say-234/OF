"""Leviers d'optimisation légale avant la clôture (UC03) et leur simulation.

Chaque fonction reçoit les paramètres d'un levier et renvoie un EffetLevier :
des écritures prévisionnelles (ajustements) et des messages de conformité au CGI.
simuler() recalcule l'IS avec et sans les leviers : le gain affiché tient compte
du minimum de perception (un levier peut n'avoir AUCUN effet sur l'impôt).
Seuils et coefficients sont lus dans referentiel/2026/leviers.yaml.
"""
from dataclasses import dataclass, replace
from decimal import Decimal

from ..balance import Balance
from ..dossier import Ajustement, Dossier
from ..montant import ZERO, arrondir_fcfa, en_pourcentage, en_texte
from ..referentiel import Referentiel
from ..resultat import ResultatFiscal
from .impot import calculer_is

MOIS = ("janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre",
        "novembre", "décembre")


@dataclass(frozen=True)
class EffetLevier:
    id_levier: str
    libelle: str
    article: str
    ajustements: tuple[Ajustement, ...]      # montant > 0 = charge supplémentaire
    decaissement: Decimal                    # sortie de trésorerie liée à la décision
    conformite: tuple[str, ...]              # messages de conformité (OK, à faire, non éligible)
    bloquant: bool = False                   # conditions légales non remplies : le levier n'est pas retenu
    decale_l_impot: bool = False             # amortissement accéléré/dégressif : décalage, pas économie


@dataclass(frozen=True)
class Simulation:
    reference: ResultatFiscal
    simulation: ResultatFiscal
    gain_is: Decimal
    decaissement: Decimal
    cout_net: Decimal
    lecture: tuple[str, ...]                 # explications par modèles de phrases (sans IA)


def _mois_restants(mois_acquisition: int) -> int:
    """Point de départ de l'amortissement : 1er jour du mois d'acquisition (art. 40)."""
    return 12 - mois_acquisition + 1


def coefficient_degressif(referentiel: Referentiel, duree: int) -> Decimal:
    tranches = referentiel.levier("L01_INVESTISSEMENT_DEGRESSIF").parametres["coefficients"]
    return next(t["coefficient"] for t in tranches if duree <= t["duree_max"])


def investissement_degressif(referentiel: Referentiel, montant_ht: Decimal, duree: int, mois_acquisition: int,
                             neuf: bool = True) -> EffetLevier:
    """L01 — art. 40 : taux linéaire × coefficient (1,5 / 2 / 2,5), prorata des mois restants."""
    p = referentiel.levier("L01_INVESTISSEMENT_DEGRESSIF").parametres
    conformite, non_eligible = [], False
    if not neuf:
        conformite.append("NON ÉLIGIBLE : le bien doit être acquis à l'état neuf (art. 40-1-a).")
        non_eligible = True
    if montant_ht < p["valeur_unitaire_min_ht"]:
        conformite.append(f"NON ÉLIGIBLE : valeur unitaire < {en_texte(Decimal(p['valeur_unitaire_min_ht']))} HT "
                          "(art. 40-1-a).")
        non_eligible = True
    if duree <= p["duree_superieure_a"]:
        conformite.append(f"NON ÉLIGIBLE : durée d'utilisation ≤ {p['duree_superieure_a']} ans (art. 40-1-b).")
        non_eligible = True
    coefficient = coefficient_degressif(referentiel, duree)
    taux_lineaire = Decimal(1) / duree
    mois = _mois_restants(mois_acquisition)
    prorata = Decimal(mois) / 12
    lineaire = arrondir_fcfa(montant_ht * taux_lineaire * prorata)
    ajustements = [Ajustement(p["compte_dotation"], "Dotation — investissement simulé (linéaire)", lineaire)]
    if non_eligible:
        conformite.append("Dégressif non applicable : seul l'amortissement linéaire est retenu dans la simulation.")
    else:
        degressif = arrondir_fcfa(montant_ht * taux_lineaire * coefficient * prorata)
        ajustements.append(Ajustement(p["compte_dotation"], "Supplément dégressif (art. 40)", degressif - lineaire))
        conformite.append(f"Conditions de l'art. 40 remplies : taux linéaire {en_pourcentage(taux_lineaire)} × "
                          f"coefficient {coefficient}, sur {mois} mois (prorata {mois}/12).")
        conformite.append("Joindre le tableau spécial des amortissements dégressifs à la déclaration (art. 40-4).")
    return EffetLevier("L01_INVESTISSEMENT_DEGRESSIF",
                       f"Investissement de {en_texte(montant_ht)} en {MOIS[mois_acquisition - 1]}", "CGI art. 40",
                       tuple(ajustements), ZERO, tuple(conformite), False, not non_eligible)


def investissement_accelere(referentiel: Referentiel, montant_ht: Decimal, duree: int, mois_acquisition: int,
                            neuf: bool = True, usage_exclusif: bool = True) -> EffetLevier:
    """L02 — art. 39 : première annuité (calculée sur la durée normale) multipliée ; durée réduite d'un an."""
    p = referentiel.levier("L02_AMORTISSEMENT_ACCELERE").parametres
    conformite, non_eligible = [], False
    if not neuf:
        conformite.append("NON ÉLIGIBLE : le matériel doit être neuf (art. 39-1).")
        non_eligible = True
    if not usage_exclusif:
        conformite.append("NON ÉLIGIBLE : usage exclusif pour fabrication, manutention, hôtellerie, téléphonie, "
                          "transport ou exploitation agricole (art. 39-1-a).")
        non_eligible = True
    if duree <= p["duree_superieure_a"]:
        conformite.append(f"NON ÉLIGIBLE : durée de vie ≤ {p['duree_superieure_a']} ans (art. 39-1-b).")
        non_eligible = True
    mois = _mois_restants(mois_acquisition)
    lineaire = arrondir_fcfa(montant_ht / duree * mois / 12)
    multiplicateur = Decimal(p["multiplicateur_premiere_annuite"])
    ajustements = [Ajustement(p["compte_dotation"], "Dotation — investissement simulé (linéaire)", lineaire)]
    if non_eligible:
        conformite.append("Accéléré non applicable : seul l'amortissement linéaire est retenu dans la simulation.")
    else:
        ajustements.append(Ajustement(p["compte_dotation"], "Supplément accéléré (art. 39)",
                                      lineaire * (multiplicateur - 1)))
        conformite.append(f"Conditions de l'art. 39 remplies : première annuité × {multiplicateur} "
                          f"({en_texte(lineaire * multiplicateur)} sur {mois} mois), durée ramenée à {duree - 1} ans.")
    return EffetLevier("L02_AMORTISSEMENT_ACCELERE",
                       f"Investissement de {en_texte(montant_ht)} en {MOIS[mois_acquisition - 1]}", "CGI art. 39",
                       tuple(ajustements), ZERO, tuple(conformite), False, not non_eligible)


def provision(referentiel: Referentiel, montant: Decimal, justifiee: bool, au_releve: bool) -> EffetLevier:
    """L03 — art. 41 : perte ou charge nettement précisée, probable, portée au relevé des provisions."""
    p = referentiel.levier("L03_PROVISION_JUSTIFIEE").parametres
    conformite, bloquant = [], False
    if not justifiee:
        conformite.append("BLOQUANT : perte ou charge non nettement précisée ou non probable (art. 41-1-a).")
        bloquant = True
    if not au_releve:
        conformite.append("À FAIRE : porter la provision au relevé des provisions (art. 41-1-a).")
    if not bloquant:
        conformite.append("Reprise imposable si la provision devient sans objet (art. 41-2).")
    ajustements = () if bloquant else (Ajustement(p["compte_dotation"], "Provision pour risque (simulée)", montant),)
    return EffetLevier("L03_PROVISION_JUSTIFIEE", f"Provision de {en_texte(montant)}", "CGI art. 41",
                       ajustements, ZERO, tuple(conformite), bloquant)


def dons_deja_comptabilises(referentiel: Referentiel, balance_projetee: Balance) -> Decimal:
    regle = referentiel.regle(referentiel.levier("L04_DONS_PLAFOND").parametres["regle_plafond"])
    return balance_projetee.total_charges(regle.comptes)


def marge_dons(referentiel: Referentiel, deja_comptabilises: Decimal, chiffre_affaires: Decimal,
               vers_etat_secteurs_eligibles: bool = False) -> Decimal:
    """Plafond de l'art. 32 non encore utilisé : 1 ‰ du CA HT (+ 25 M pour certains dons à l'État)."""
    p = referentiel.levier("L04_DONS_PLAFOND").parametres
    plafond = referentiel.regle(p["regle_plafond"]).taux_plafond * chiffre_affaires
    if vers_etat_secteurs_eligibles:
        plafond += referentiel.regle(p["regle_supplement"]).plafond_montant
    return max(ZERO, plafond - deja_comptabilises)


def dons(referentiel: Referentiel, montant: Decimal, deja_comptabilises: Decimal, chiffre_affaires: Decimal,
         vers_etat_secteurs_eligibles: bool) -> EffetLevier:
    """L04 — art. 32 : le don reste une dépense ; l'économie d'IS réduit seulement son coût net."""
    p = referentiel.levier("L04_DONS_PLAFOND").parametres
    marge = marge_dons(referentiel, deja_comptabilises, chiffre_affaires, vers_etat_secteurs_eligibles)
    conformite = [f"Déjà utilisé : {en_texte(deja_comptabilises)} ; marge restante : {en_texte(marge)}."]
    if montant > marge:
        conformite.append(f"ATTENTION : {en_texte(montant - marge)} dépasseront le plafond et seront réintégrés.")
    if vers_etat_secteurs_eligibles:
        conformite.append("Joindre la preuve de réception du don à la déclaration (art. 32-2).")
    return EffetLevier("L04_DONS_PLAFOND", f"Don de {en_texte(montant)}", "CGI art. 32",
                       (Ajustement(p["compte_charge"], "Don (simulé)", montant),), montant, tuple(conformite))


def charges_anticipees(referentiel: Referentiel, montant: Decimal, nature: str, reglement_especes: bool) -> EffetLevier:
    """L05 — art. 20 et 23-2 : charge engagée dans l'exercice, sur facture normalisée, sans espèces ≥ 100 000."""
    p = referentiel.levier("L05_CHARGES_ANTICIPEES").parametres
    param = referentiel.parametres
    conformite = ["Charge à engager dans l'exercice, dans l'intérêt de l'exploitation, sur facture normalisée "
                  "(art. 20)."]
    bloquant = False
    if reglement_especes and montant >= param.seuil_especes:
        conformite.append(f"BLOQUANT : règlement en espèces interdit à partir de {en_texte(param.seuil_especes)} "
                          f"(art. 21). Sanction : droit de timbre de {en_pourcentage(param.taux_timbre_especes)}, "
                          f"soit {en_texte(montant * param.taux_timbre_especes)} (art. 423-4 et 503-1). "
                          "Prévoir un virement ou un chèque.")
        bloquant = True
    ajustements = () if bloquant else (Ajustement(p["compte_charge"], f"{nature} (anticipée)", montant),)
    return EffetLevier("L05_CHARGES_ANTICIPEES", f"{nature} : {en_texte(montant)}", "CGI art. 20 et 23-2",
                       ajustements, montant, tuple(conformite), bloquant)


def simuler(balance: Balance, dossier: Dossier, referentiel: Referentiel, effets: list[EffetLevier]) -> Simulation:
    """Compare l'IS sans leviers et avec les leviers retenus (les leviers bloquants sont ignorés)."""
    retenus = [e for e in effets if not e.bloquant]
    reference = calculer_is(balance, dossier, referentiel)
    ajustements = dossier.hypotheses.ajustements + tuple(a for e in retenus for a in e.ajustements)
    avec_leviers = replace(dossier, hypotheses=replace(dossier.hypotheses, ajustements=ajustements))
    simulation = calculer_is(balance, avec_leviers, referentiel)
    gain = reference.is_du - simulation.is_du
    decaissement = sum((e.decaissement for e in retenus), ZERO)
    lecture = []
    if reference.au_minimum and gain < 1:
        lecture.append("Aucun gain d'IS : le minimum de perception s'applique avant comme après. Réduire le "
                       "résultat fiscal est inutile cette année ; privilégier les leviers de trésorerie (acomptes).")
    elif simulation.au_minimum and not reference.au_minimum:
        lecture.append(f"Le levier fait basculer l'entreprise au minimum de perception : le gain est plafonné à "
                       f"{en_texte(gain)}. Au-delà, les charges supplémentaires n'ont plus d'effet fiscal.")
    if any(e.decale_l_impot for e in retenus):
        lecture.append("L'amortissement dégressif ou accéléré DÉCALE l'impôt dans le temps (annuités plus faibles "
                       "ensuite) : c'est un gain de trésorerie, pas une économie définitive.")
    return Simulation(reference, simulation, gain, decaissement, decaissement - gain, tuple(lecture))
