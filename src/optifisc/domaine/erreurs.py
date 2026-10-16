"""Exceptions métier.

Chaque erreur qu'un utilisateur peut rencontrer a son propre type : l'interface
les attrape et affiche le message (en français), jamais une trace Python.
"""


class ErreurMetier(Exception):
    """Classe mère de toutes les erreurs métier d'OptiFisc."""


class DonneeInvalide(ErreurMetier):
    """Une donnée ne respecte pas une règle de cohérence (montant float, compte vide…)."""


class BalanceIllisible(ErreurMetier):
    """Le fichier de balance ne peut pas être lu (colonnes introuvables, format inconnu…)."""


class ReferentielInvalide(ErreurMetier):
    """Un fichier du référentiel (YAML) est mal formé ou incomplet."""


class AccesRefuse(ErreurMetier):
    """L'utilisateur n'a pas le droit de faire cette action (doc 02)."""


class DossierFige(ErreurMetier):
    """Le dossier est à valider, validé ou livré : il ne peut plus être modifié."""


class TransitionInterdite(ErreurMetier):
    """Le changement d'état demandé n'est pas permis par le cycle de vie du dossier."""


class EtapeIncomplete(ErreurMetier):
    """Une étape préalable manque (ex. calculer sans balance, soumettre avec des saisies vides)."""
