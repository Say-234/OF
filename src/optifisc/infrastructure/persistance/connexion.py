"""Accès à la base SQLite locale et application des migrations.

Chaque opération ouvre une connexion courte, la valide puis la FERME (la V2 laissait
les connexions ouvertes). Les migrations sont des fichiers SQL numérotés, appliqués
une seule fois ; le numéro de la dernière appliquée est rangé dans PRAGMA user_version.
"""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

MIGRATIONS = Path(__file__).parent / "migrations"


class BaseSqlite:
    def __init__(self, chemin: Path | str):
        self.chemin = Path(chemin)
        self.chemin.parent.mkdir(parents=True, exist_ok=True)
        self._migrer()

    @contextmanager
    def connexion(self):
        cx = sqlite3.connect(self.chemin)
        cx.execute("PRAGMA foreign_keys = ON")
        try:
            yield cx
            cx.commit()
        except Exception:
            cx.rollback()
            raise
        finally:
            cx.close()

    def _migrer(self) -> None:
        with self.connexion() as cx:
            version = cx.execute("PRAGMA user_version").fetchone()[0]
            for fichier in sorted(MIGRATIONS.glob("*.sql")):
                numero = int(fichier.name.split("_")[0])
                if numero > version:
                    cx.executescript(fichier.read_text(encoding="utf-8"))
                    cx.execute(f"PRAGMA user_version = {numero}")
