"""Recherche d'articles par mots-clés (BM25), locale et sans IA (implémente le port RechercheArticles).

Repris de la V2 : mots normalisés (sans accents), mots vides retirés, pluriel simple ;
les articles du chapitre IS sont favorisés (le prototype porte sur l'IS) ; un article
cité dans la question (« art. 32 ») remonte en tête.
"""
import re
import unicodedata

from rank_bm25 import BM25Okapi

from optifisc.domaine.proposition import Article, ArticleTrouve

BONUS_IS = 1.5
MOTS_VIDES = set("""a au aux avec ce ces dans de des du elle en et eux il je la le les leur lui ma mais me meme mes moi
mon ne nos notre nous on ou par pas pour qu que qui sa se ses son sur ta te tes toi ton tu un une vos votre vous
est sont peut peuvent doit doivent etre ete cette cet quel quelle quels quelles comment quoi dont plus tout
tous toute toutes si leurs article articles alinea present code l d s n c j m""".split())


def _normaliser(texte: str) -> str:
    texte = unicodedata.normalize("NFKD", texte.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9%]+", " ", texte)


def mots(texte: str) -> list[str]:
    retenus = []
    for mot in _normaliser(texte).split():
        if mot in MOTS_VIDES or len(mot) < 2:
            continue
        retenus.append(mot[:-1] if len(mot) > 4 and mot.endswith("s") else mot)
    return retenus


class RechercheBm25:
    def __init__(self, articles: list[Article]):
        self.articles = articles
        self.index = BM25Okapi([mots(f"{a.texte} {a.chapitre}") for a in articles])

    def rechercher(self, question: str, k: int = 5) -> list[ArticleTrouve]:
        scores = list(self.index.get_scores(mots(question)))
        cites = set(re.findall(r"art(?:icle)?\.?\s*(\d+)", question.lower()))
        for i, article in enumerate(self.articles):
            if article.chapitre == "IS":
                scores[i] *= BONUS_IS
            if article.numero in cites and article.source.startswith("CGI"):
                scores[i] += max(scores) + 1                   # article cité : en tête
        ordre = sorted((i for i, s in enumerate(scores) if s > 0), key=lambda i: -scores[i])[:k]
        meilleur = scores[ordre[0]] if ordre else 1
        return [ArticleTrouve(self.articles[i], round(scores[i] / meilleur, 2)) for i in ordre]

    def article(self, numero: str, source: str = "CGI 2026") -> Article | None:
        return next((a for a in self.articles if a.numero == str(numero) and a.source == source), None)

    def similarite(self, texte: str, numero: str) -> float:
        """Part des mots significatifs du texte présents dans l'article (0 à 1). Sert au juge déterministe."""
        article = self.article(numero)
        if article is None:
            return 0.0
        mots_texte = set(mots(texte))
        if not mots_texte:
            return 0.0
        return round(len(mots_texte & set(mots(article.texte))) / len(mots_texte), 2)
