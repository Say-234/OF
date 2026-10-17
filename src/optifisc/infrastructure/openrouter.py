"""Fournisseur d'IA OpenRouter (implémente le port FournisseurIA), avec des modèles gratuits (suffixe :free).

Ce qui est envoyé est décidé par la couche Application (pare-feu de données) : ce module se
contente de transmettre des messages et de rapporter la réponse ou l'erreur.
Le nom du modèle est un réglage (.env), pas une valeur écrite dans le code.
"""
import time

import requests

from optifisc.domaine.erreurs import IAIndisponible

URL = "https://openrouter.ai/api/v1/chat/completions"
DELAI_SECONDES = 60
SUFFIXE_GRATUIT = ":free"      # consigne du projet : UNIQUEMENT des modèles gratuits (décision du 16/10/2026)
ATTENTE_SATURATION = 4        # secondes avant UNE nouvelle tentative quand tous les modèles sont saturés (429)


def est_gratuit(modele: str) -> bool:
    return modele.strip().endswith(SUFFIXE_GRATUIT)


class OpenRouter:
    confidentiel = False                   # service en ligne : autorisé par défaut pour les dossiers de démo seulement

    def __init__(self, cle_api: str, modele: str, temperature: float = 0.1, max_jetons: int = 2500,
                 secours: tuple[str, ...] = ()):
        self.cle_api = cle_api.strip()
        self.modele = modele.strip()
        # modèles de secours : si le modèle principal est saturé, OpenRouter bascule tout seul sur le suivant
        self.secours = tuple(m.strip() for m in secours if m.strip() and m.strip() != self.modele)
        self.temperature = temperature
        self.max_jetons = max_jetons

    @property
    def disponible(self) -> bool:
        return bool(self.cle_api and self.modele and est_gratuit(self.modele))

    @property
    def nom(self) -> str:
        return f"OpenRouter · {self.modele}"

    def discuter(self, messages: list[dict]) -> str:
        for modele in (self.modele, *self.secours):
            if modele and not est_gratuit(modele):
                raise IAIndisponible(f"Modèle refusé : « {modele} » n'est pas un modèle gratuit (suffixe :free). "
                                     "Seuls les modèles gratuits sont autorisés.")
        if not self.disponible:
            raise IAIndisponible("IA non configurée : renseignez OPENROUTER_API_KEY et le modèle dans .env.")
        corps = {"model": self.modele, "messages": messages, "temperature": self.temperature,
                 "max_tokens": self.max_jetons,
                 # modèles « qui réfléchissent » (ex. Nemotron) : réflexion courte, sinon elle consomme tout le
                 # budget de jetons et la réponse arrive vide ; ignoré par les modèles qui ne réfléchissent pas
                 "reasoning": {"effort": "low", "exclude": True}}
        if self.secours:
            corps["models"] = [self.modele, *self.secours]       # bascule automatique d'OpenRouter
        reponse = self._envoyer(corps)
        if reponse.status_code == 429:                           # tous saturés : une seule nouvelle tentative
            time.sleep(ATTENTE_SATURATION)
            reponse = self._envoyer(corps)
        if reponse.status_code == 404:
            raise IAIndisponible("Modèle introuvable ou bloqué par vos réglages de confidentialité OpenRouter "
                                 "(les modèles gratuits exigent d'autoriser leurs fournisseurs).")
        if reponse.status_code == 429:
            raise IAIndisponible("Les modèles gratuits sont saturés en ce moment (limite d'appels d'OpenRouter) : "
                                 "réessayez dans une minute. Les articles trouvés ci-dessus restent valables.")
        if reponse.status_code != 200:
            raise IAIndisponible(f"Le service d'IA a répondu par une erreur ({reponse.status_code}).")
        try:
            texte = reponse.json()["choices"][0]["message"]["content"] or ""
        except (ValueError, KeyError, IndexError) as exc:
            raise IAIndisponible("Réponse du service d'IA illisible.") from exc
        if not texte.strip():
            raise IAIndisponible("Le modèle gratuit a renvoyé une réponse vide : réessayez dans un instant.")
        return texte

    def _envoyer(self, corps: dict):
        try:
            return requests.post(URL, timeout=DELAI_SECONDES, json=corps,
                                 headers={"Authorization": f"Bearer {self.cle_api}", "X-Title": "OptiFisc"})
        except requests.RequestException as exc:
            raise IAIndisponible(f"Service d'IA injoignable ({type(exc).__name__}). Vérifiez la connexion.") from exc
