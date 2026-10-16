"""Sauvegarde de la base du cabinet (doc 06, §4.3).

Utilise l'API de sauvegarde de SQLite : la copie est cohérente même si l'application est ouverte.
Usage :  python scripts/sauvegarder.py [dossier_de_destination]
Par défaut, les copies vont dans var/sauvegardes/ ; mieux vaut un disque externe ou un dossier synchronisé.
"""
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
BASE = RACINE / "var" / "optifisc_cabinet.sqlite"


def sauvegarder(destination: Path) -> Path:
    if not BASE.exists():
        raise SystemExit(f"Base introuvable : {BASE}")
    destination.mkdir(parents=True, exist_ok=True)
    cible = destination / f"optifisc_{datetime.now():%Y%m%d_%H%M%S}.sqlite"
    with sqlite3.connect(BASE) as source, sqlite3.connect(cible) as copie:
        source.backup(copie)
    return cible


if __name__ == "__main__":
    dossier = Path(sys.argv[1]) if len(sys.argv) > 1 else RACINE / "var" / "sauvegardes"
    print(f"Sauvegarde écrite : {sauvegarder(dossier)}")
