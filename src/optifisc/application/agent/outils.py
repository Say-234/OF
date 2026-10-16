"""Les outils offerts à l'agent : des fonctions ÉCRITES ET CONTRÔLÉES PAR NOUS (UC14).

L'agent ne peut rien faire d'autre que ce que ces fonctions permettent. Aucune ne lui donne
accès à la raison sociale, à la balance détaillée ou à un libellé de compte.
"""
from optifisc.domaine.balance import Balance
from optifisc.domaine.dossier import Dossier
from optifisc.domaine.moteur.leviers import simuler
from optifisc.domaine.proposition import ProfilPseudonymise
from optifisc.domaine.referentiel import Referentiel
from optifisc.domaine.resultat import ResultatFiscal
from optifisc.domaine.scenario import LevierChoisi

from ..ports import RechercheArticles
from ..scenarios import effet_du_levier
from .juge import JugeDeterministe
from .profil import millions

PROPOSITIONS_MAXIMUM = 5


def construire_outils(profil: ProfilPseudonymise, juge: JugeDeterministe, recherche: RechercheArticles,
                      referentiel: Referentiel, balance: Balance, dossier: Dossier, resultat: ResultatFiscal,
                      propositions: list[dict]) -> dict:
    """Renvoie {nom de l'outil: fonction(arguments) -> texte}. Les propositions reçues s'ajoutent à `propositions`."""

    def lire_profil(arguments: dict) -> str:
        return profil.en_texte()

    def lister_leviers(arguments: dict) -> str:
        lignes = []
        for p in juge.pre_trier(profil):
            lignes.append(f"{p.levier.id} — {p.levier.libelle} ({p.levier.article}) — pertinence {p.score} : "
                          f"{' ; '.join(p.raisons)}")
        return "\n".join(lignes)

    def rechercher_articles(arguments: dict) -> str:
        trouves = recherche.rechercher(str(arguments.get("question", "")), 3)
        return "\n\n".join(f"Article {t.article.numero} ({t.article.chapitre}) : {t.article.texte[:700]}"
                           for t in trouves) or "Aucun article trouvé."

    def simuler_levier(arguments: dict) -> str:
        choix = LevierChoisi(str(arguments.get("id_levier", "")), dict(arguments.get("parametres") or {}))
        effet = effet_du_levier(referentiel, choix, resultat)
        simulation = simuler(balance, dossier, referentiel, [effet])
        gain = millions(simulation.gain_is)
        nature = "décalage d'impôt" if effet.decale_l_impot else "économie"
        return (f"Gain d'IS estimé par le moteur : environ {gain} million(s) FCFA ({nature}). "
                f"Conditions : {' '.join(effet.conformite)} " + " ".join(simulation.lecture))

    def proposer(arguments: dict) -> str:
        if len(propositions) >= PROPOSITIONS_MAXIMUM:
            return f"Limite de {PROPOSITIONS_MAXIMUM} propositions atteinte : termine par {{\"fin\": true}}."
        propositions.append(dict(arguments))
        return f"Proposition {len(propositions)} enregistrée."

    return {"lire_profil": lire_profil, "lister_leviers": lister_leviers, "rechercher_articles": rechercher_articles,
            "simuler_levier": simuler_levier, "proposer": proposer}

