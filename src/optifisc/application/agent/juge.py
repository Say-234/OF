"""JugeDeterministe — le « Système 1 » maison (doc 01, A.4, décision du 16/10/2026).

Gratuit, instantané, hors ligne et EXPLICABLE : chaque score est une somme de contrôles
vérifiables, et le détail de chaque contrôle est affiché à l'utilisateur.
Il implémente le port ModeleDecision : Jev ou un Laya spécialisé pourraient le remplacer plus tard.
"""
from dataclasses import dataclass
from decimal import Decimal

from optifisc.domaine.proposition import ProfilPseudonymise
from optifisc.domaine.referentiel import Levier, Referentiel

from ..ports import RechercheArticles

SEUIL_CONFIANCE = Decimal("0.70")          # en dessous : badge « confiance faible — vérifier en priorité »


@dataclass(frozen=True)
class Pertinence:
    levier: Levier
    score: Decimal
    raisons: tuple[str, ...]


def critere_rempli(critere: str, profil: ProfilPseudonymise) -> tuple[bool, str]:
    """Critères de pertinence écrits dans leviers.yaml, évalués sur le profil pseudonymisé."""
    if critere == "au_dessus_du_seuil":
        ok = not profil.au_minimum_de_perception and profil.ecart_au_seuil_millions > 0
        if ok:
            return True, "réduire le résultat réduit l'impôt"
        return False, "minimum de perception : réduire le résultat est sans effet"
    if critere == "mois_restants":
        ok = profil.mois_arrete < 12
        return ok, "il reste des mois avant la clôture" if ok else "exercice clos"
    if critere == "marge_dons":
        ok = profil.dons_marge_millions > 0
        return ok, "marge de plafond de dons disponible" if ok else "plafond de dons déjà atteint"
    if critere == "surpaiement_acomptes":
        ok = profil.excedent_acomptes_millions > 0
        return ok, "acomptes supérieurs à l'impôt estimé" if ok else "pas d'excédent d'acomptes"
    return False, f"critère inconnu : {critere}"


class JugeDeterministe:
    def __init__(self, referentiel: Referentiel, recherche: RechercheArticles):
        self.referentiel = referentiel
        self.recherche = recherche

    def pre_trier(self, profil: ProfilPseudonymise) -> list[Pertinence]:
        """Pertinence de chaque levier du catalogue pour ce profil (part des critères remplis)."""
        resultats = []
        for levier in self.referentiel.leviers:
            evaluations = [critere_rempli(c, profil) for c in levier.pertinence]
            remplis = sum(ok for ok, _ in evaluations)
            score = Decimal(remplis) / len(evaluations) if evaluations else Decimal(0)
            resultats.append(Pertinence(levier, score.quantize(Decimal("0.01")), tuple(r for _, r in evaluations)))
        return sorted(resultats, key=lambda p: -p.score)

    def juger(self, article: str, justification: str, levier_bloquant: bool | None) -> tuple[Decimal, tuple[str, ...]]:
        """Confiance (0 à 1) d'une proposition et détail des contrôles.

        levier_bloquant : None pour une piste (pas de levier), sinon True si les conditions légales échouent.
        """
        trouve = self.recherche.article(article)
        if trouve is None:
            return Decimal(0), (f"✗ l'article {article} n'existe pas dans le CGI 2026 : proposition rejetée",)
        controles, score = [f"✓ article {article} trouvé dans le CGI 2026"], Decimal("0.3")
        if trouve.chapitre == "IS":
            score += Decimal("0.2")
            controles.append("✓ article du chapitre « impôt sur les sociétés »")
        else:
            controles.append(f"▲ article hors du chapitre IS ({trouve.chapitre or 'chapitre non identifié'})")
        similarite = Decimal(str(self.recherche.similarite(justification, article)))
        score += Decimal("0.3") * similarite
        controles.append(f"{'✓' if similarite >= Decimal('0.4') else '▲'} vocabulaire commun avec l'article : "
                         f"{int(similarite * 100)} %")
        if levier_bloquant is None:
            score += Decimal("0.1")
            controles.append("▲ piste non chiffrée : à étudier par le cabinet")
        elif levier_bloquant:
            controles.append("✗ conditions légales du levier non remplies avec ces paramètres")
        else:
            score += Decimal("0.2")
            controles.append("✓ conditions légales du levier remplies ; gain calculé par le moteur")
        return min(score, Decimal(1)).quantize(Decimal("0.01")), tuple(controles)
