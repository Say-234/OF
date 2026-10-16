"""Chargement des articles du CGI 2026 et du LPF 2024 (fichiers JSON découpés par article)."""
import json
import re
from pathlib import Path

from optifisc.domaine.proposition import Article


def chapitre(contexte: str) -> str:
    """« LIVRE 1 > CHAPITRE 1 IMPOT SUR LES SOCIÉTÉS (IS) > … » → « IS » ; sinon le titre du chapitre."""
    for partie in contexte.split(" > "):
        if partie.upper().startswith(("CHAPITRE", "TITRE")):
            sigle = re.search(r"\(([^)]+)\)", partie)
            if sigle:
                return sigle.group(1).strip()
            return re.sub(r"^(CHAPITRE|TITRE)\s+\S+\s*", "", partie, flags=re.I).strip().capitalize()
    return ""


def charger_corpus(dossier: Path) -> list[Article]:
    articles = []
    for fichier in sorted(Path(dossier).glob("*.json")):
        for brut in json.loads(fichier.read_text(encoding="utf-8")):
            articles.append(Article(source=brut["source"], numero=str(brut["article"]),
                                    chapitre=chapitre(brut.get("contexte", "")), texte=brut["texte"]))
    return articles
