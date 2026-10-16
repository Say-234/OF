"""Fournisseur d'IA OpenRouter (implémente le port FournisseurIA), avec des modèles gratuits (suffixe :free).

Ce qui est envoyé est décidé par la couche Application (pare-feu de données) : ce module se
contente de transmettre des messages et de rapporter la réponse ou l'erreur.
Le nom du modèle est un réglage (.env), pas une valeur écrite dans le code.
"""
import requests

from optifisc.domaine.erreurs import IAIndisponible

URL = "https://openrouter.ai/api/v1/chat/completions"
DELAI_SECONDES = 60


class OpenRouter:
    confidentiel = False                   # service en ligne : autorisé par défaut pour les dossiers de démo seulement

    def __init__(self, cle_api: str, modele: str, temperature: float = 0.1, max_jetons: int = 900):
        self.cle_api = cle_api.strip()
        self.modele = modele.strip()
        self.temperature = temperature
        self.max_jetons = max_jetons

    @property
    def disponible(self) -> bool:
        return bool(self.cle_api and self.modele)

    @property
    def nom(self) -> str:
        return f"OpenRouter · {self.modele}"

    def discuter(self, messages: list[dict]) -> str:
        if not self.disponible:
            raise IAIndisponible("IA non configurée : renseignez OPENROUTER_API_KEY et OPENROUTER_MODELE dans .env.")
        try:
            reponse = requests.post(
                URL, timeout=DELAI_SECONDES,
                headers={"Authorization": f"Bearer {self.cle_api}", "X-Title": "OptiFisc"},
                json={"model": self.modele, "messages": messages, "temperature": self.temperature,
                      "max_tokens": self.max_jetons})
        except requests.RequestException as exc:
            raise IAIndisponible(f"Service d'IA injoignable ({type(exc).__name__}). Vérifiez la connexion.") from exc
        if reponse.status_code == 429:
            raise IAIndisponible("Limite d'appels du modèle gratuit atteinte : réessayez dans une minute.")
        if reponse.status_code != 200:
            raise IAIndisponible(f"Le service d'IA a répondu par une erreur ({reponse.status_code}).")
        try:
            return reponse.json()["choices"][0]["message"]["content"] or ""
        except (ValueError, KeyError, IndexError) as exc:
            raise IAIndisponible("Réponse du service d'IA illisible.") from exc
