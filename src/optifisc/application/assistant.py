"""UC09 — Assistant CGI : recherche locale d'articles, puis réponse rédigée par l'IA À PARTIR DE CES SEULS ARTICLES.

Pare-feu de données (doc 01, A.3) : la question n'est envoyée au service d'IA que si elle ne semble
contenir aucune donnée client (montant, numéro d'identification, nom d'un client connu).
"""
import re
import time

from optifisc.domaine.erreurs import IAIndisponible
from optifisc.domaine.proposition import ReponseAssistant
from optifisc.domaine.utilisateur import Utilisateur

from .autorisation import exiger
from .dependances import Dependances
from .ports import FournisseurIA, RechercheArticles

PROMPT_SYSTEME = """Tu es l'assistant fiscal d'un cabinet d'expertise comptable au Bénin. Tu réponds aux questions sur l'impôt sur les sociétés (IS) et les procédures fiscales, à partir des extraits du Code général des impôts (CGI 2026) et du Livre des procédures fiscales (LPF 2024) fournis.

Règles strictes :
1. Réponds UNIQUEMENT à partir des extraits fournis, sans aucune autre connaissance.
2. Lis chaque extrait avant de conclure qu'il ne répond pas : la formulation peut différer de la question.
3. Réponds avec exactement cette structure, sans rien d'autre :
Réponse : <explication complète en français, avec les taux, montants ou conditions exacts tirés des extraits>
Article(s) : <numéros des articles utilisés, séparés par des virgules ; « aucun » si tu n'as pas pu répondre>
4. Si aucun extrait ne traite la question : « Réponse : Je ne trouve pas de disposition traitant de cette question dans les articles fournis. » et « Article(s) : aucun »."""

MONTANT = re.compile(r"\d[\d\s.  ]{4,}\d")      # 5 chiffres ou plus (ex. 1 500 000) : probable montant client


def probleme_pare_feu(question: str, noms_clients: list[str]) -> str:
    """Renvoie la raison du blocage, ou "" si la question peut être envoyée au service d'IA."""
    texte = question.lower()
    if MONTANT.search(question):
        return "la question contient un nombre qui ressemble à un montant ou à un identifiant"
    for nom in noms_clients:
        if nom and nom.lower() in texte:
            return f"la question mentionne un client du cabinet (« {nom} »)"
    return ""


def lire_reponse(brut: str) -> tuple[str, list[str]]:
    """Sépare « Réponse : … » et « Article(s) : … » ; tolère un format approximatif."""
    m_reponse = re.search(r"R[ée]ponse\s*:\s*(.+?)(?:\s*Article\(s\)\s*:|$)", brut, re.S | re.I)
    m_articles = re.search(r"Article\(s\)\s*:\s*(.+)", brut, re.I)
    articles = [] if not m_articles or "aucun" in m_articles.group(1).lower() \
        else re.findall(r"\d+(?:-\d+)?", m_articles.group(1))
    return (m_reponse.group(1) if m_reponse else brut).strip(), articles


class ServiceAssistant:
    def __init__(self, dep: Dependances, recherche: RechercheArticles, fournisseur: FournisseurIA):
        self.dep = dep
        self.recherche = recherche
        self.fournisseur = fournisseur

    def poser(self, utilisateur: Utilisateur | None, question: str, avec_ia: bool = True) -> ReponseAssistant:
        exiger(utilisateur, "interroger_assistant")
        question = question.strip()
        trouves = tuple(self.recherche.rechercher(question, 5)) if question else ()
        if not question or not avec_ia:
            return ReponseAssistant(question, trouves)
        if not self.fournisseur.disponible:
            return ReponseAssistant(question, trouves, message="IA désactivée : seuls les articles trouvés "
                                                               "localement sont affichés.")
        probleme = probleme_pare_feu(question, [d.raison_sociale for d in self.dep.dossiers.lister()])
        if probleme:
            self.dep.tracer(utilisateur, "ia_bloquee_pare_feu", probleme)
            return ReponseAssistant(question, trouves, message=f"Question non envoyée à l'IA : {probleme}. "
                                                               "Reformulez sans donnée du client.")
        extraits = "\n\n".join(f"{t.article.source} — article {t.article.numero} ({t.article.chapitre}) :\n"
                               f"{t.article.texte[:3000]}" for t in trouves)
        messages = [{"role": "system", "content": PROMPT_SYSTEME},
                    {"role": "user", "content": f"Extraits :\n\n{extraits}\n\nQuestion : {question}"}]
        debut = time.monotonic()
        try:
            brut = self.fournisseur.discuter(messages)
        except IAIndisponible as exc:
            return ReponseAssistant(question, trouves, message=str(exc))
        reponse, cites = lire_reponse(brut)
        fournis = {t.article.numero for t in trouves}
        self.dep.tracer(utilisateur, "appel_ia", f"assistant · {self.fournisseur.nom} · {time.monotonic() - debut:.0f} s"
                                                 f" · question : {question[:150]} · articles fournis : "
                                                 f"{', '.join(sorted(fournis))}")
        return ReponseAssistant(question, trouves, reponse, tuple(cites),
                                sourcee=any(c.split("-")[0] in fournis for c in cites), modele=self.fournisseur.nom)
