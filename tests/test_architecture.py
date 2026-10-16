"""Garde-fou de l'architecture en 4 couches (doc 07, §1).

Ce test lit les imports de chaque fichier Python sans l'exécuter (module ast)
et échoue si une couche importe ce qui lui est interdit.
"""
import ast
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src" / "optifisc"

# Bibliothèques techniques interdites au cœur métier (domaine et application)
TECHNIQUES = {"streamlit", "sqlite3", "openpyxl", "xlrd", "yaml", "pydantic", "requests", "docx",
              "rank_bm25", "pandas", "dotenv"}

# Pour chaque couche : les modules optifisc qu'elle n'a pas le droit d'importer
INTERDITS_INTERNES = {
    "domaine": {"optifisc.application", "optifisc.infrastructure", "optifisc.interface", "optifisc.composition"},
    "application": {"optifisc.infrastructure", "optifisc.interface", "optifisc.composition"},
    "infrastructure": {"optifisc.interface", "optifisc.composition"},
    "interface": {"optifisc.infrastructure"},
}


def imports_du_fichier(chemin: Path) -> set[str]:
    """Renvoie les noms complets des modules importés par un fichier."""
    arbre = ast.parse(chemin.read_text(encoding="utf-8"))
    noms = set()
    for noeud in ast.walk(arbre):
        if isinstance(noeud, ast.Import):
            noms.update(alias.name for alias in noeud.names)
        elif isinstance(noeud, ast.ImportFrom) and noeud.module and noeud.level == 0:
            noms.add(noeud.module)
    return noms


def fichiers_de(couche: str) -> list[Path]:
    return sorted((SRC / couche).rglob("*.py"))


@pytest.mark.parametrize("couche", ["domaine", "application"])
def test_coeur_metier_sans_bibliotheque_technique(couche):
    for fichier in fichiers_de(couche):
        for module in imports_du_fichier(fichier):
            racine = module.split(".")[0]
            assert racine not in TECHNIQUES, f"{fichier.relative_to(SRC)} importe {module}"


@pytest.mark.parametrize("couche", list(INTERDITS_INTERNES))
def test_regle_de_dependance_entre_couches(couche):
    for fichier in fichiers_de(couche):
        for module in imports_du_fichier(fichier):
            for interdit in INTERDITS_INTERNES[couche]:
                assert not module.startswith(interdit), f"{fichier.relative_to(SRC)} importe {module}"
