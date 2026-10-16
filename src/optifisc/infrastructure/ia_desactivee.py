"""Fournisseur d'IA « désactivé » : l'application fonctionne entièrement sans IA (recherche d'articles locale)."""
from optifisc.domaine.erreurs import IAIndisponible


class IADesactivee:
    disponible = False
    nom = "IA désactivée"
    confidentiel = True

    def discuter(self, messages: list[dict]) -> str:
        raise IAIndisponible("L'IA est désactivée sur ce poste (OPTIFISC_IA=desactivee).")
