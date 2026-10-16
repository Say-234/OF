"""Mots de passe : hachage PBKDF2-SHA256 salé, vérification en temps constant, politique (doc 02, §5.3).

On ne stocke JAMAIS un mot de passe : seulement un sel aléatoire et une empreinte.
Si la base est volée, les mots de passe ne le sont pas.
"""
import hashlib
import hmac
import secrets

ITERATIONS = 310_000
LONGUEUR_MINIMALE = 8                    # décision D2.7 (14/10/2026)
COURANTS = {"motdepasse", "password", "12345678", "123456789", "azertyui", "azerty123", "qwertyui",
            "00000000", "11111111", "cabinet1", "optifisc", "bienvenue", "demo2026"}


class MotsDePassePbkdf2:
    """Implémente le port ServiceMotsDePasse."""

    def hacher(self, mot_de_passe: str) -> tuple[str, str]:
        sel = secrets.token_hex(16)
        return sel, self._empreinte(mot_de_passe, sel)

    def verifier(self, mot_de_passe: str, sel: str, empreinte: str) -> bool:
        # compare_digest prend le même temps que les chaînes soient proches ou non (attaque par mesure du temps)
        return hmac.compare_digest(self._empreinte(mot_de_passe, sel), empreinte)

    def generer(self) -> str:
        """Mot de passe initial aléatoire (12 caractères lisibles), à changer à la première connexion."""
        alphabet = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        return "".join(secrets.choice(alphabet) for _ in range(12))

    def probleme(self, mot_de_passe: str) -> str | None:
        if len(mot_de_passe) < LONGUEUR_MINIMALE:
            return f"au moins {LONGUEUR_MINIMALE} caractères"
        if mot_de_passe.lower() in COURANTS:
            return "mot de passe trop courant"
        return None

    @staticmethod
    def _empreinte(mot_de_passe: str, sel: str) -> str:
        return hashlib.pbkdf2_hmac("sha256", mot_de_passe.encode(), bytes.fromhex(sel), ITERATIONS).hex()
