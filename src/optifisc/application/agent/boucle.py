"""La boucle de l'agent (UC14), écrite sans framework pour que chaque étape soit lisible (décision D3.7).

Protocole simple, compatible avec n'importe quel modèle : à chaque tour, le modèle répond par UN objet JSON.
  {"outil": "<nom>", "arguments": {...}}   → notre code exécute l'outil et lui renvoie le résultat
  {"fin": true}                            → l'agent a terminé
Les limites (tours, durée) sont imposées par le code, pas demandées au modèle.
"""
import json
import re
import time
from dataclasses import dataclass, field

from optifisc.domaine.erreurs import IAIndisponible

from ..ports import FournisseurIA

TOURS_MAXIMUM = 10
DUREE_MAXIMUM_SECONDES = 90

CONSIGNE = """Tu es un agent d'aide à l'optimisation fiscale LÉGALE de l'impôt sur les sociétés au Bénin (CGI 2026), au service d'un cabinet d'expertise comptable. Ta mission : proposer 3 à 5 pistes d'optimisation pour le dossier décrit par le profil, y compris des pistes hors du catalogue de leviers.

Tu ne calcules JAMAIS de montant : pour chiffrer un levier du catalogue, utilise l'outil simuler_levier ; le moteur de l'application calcule. Ne recopie aucun montant dans tes justifications.

À chaque tour, réponds par UN SEUL objet JSON, sans texte autour :
{"outil": "lire_profil", "arguments": {}}
{"outil": "lister_leviers", "arguments": {}}
{"outil": "rechercher_articles", "arguments": {"question": "..."}}
{"outil": "simuler_levier", "arguments": {"id_levier": "L03_PROVISION_JUSTIFIEE", "parametres": {"montant": "5000000", "justifiee": true, "au_releve": true}}}
{"outil": "proposer", "arguments": {"type": "levier" ou "piste", "titre": "...", "article": "numéro de l'article du CGI", "justification": "raisonnement en une ou deux phrases", "id_levier": "seulement pour un levier", "parametres": {}}}
{"fin": true}

Paramètres des leviers : L01/L02 {"montant", "duree", "mois_acquisition", "neuf"} ; L03 {"montant", "justifiee", "au_releve"} ; L04 {"montant", "vers_etat"} ; L05 {"montant", "nature", "especes"}.
Commence par lire le profil, puis la liste des leviers ; cite toujours un article réel du CGI ; termine par {"fin": true}."""


@dataclass
class Trace:
    """Journal lisible de ce que l'agent a fait (affiché à l'utilisateur et tracé dans le journal d'audit)."""
    etapes: list[str] = field(default_factory=list)
    arret: str = ""


def lire_action(brut: str) -> dict | None:
    """Extrait le premier objet JSON de la réponse du modèle (tolère du texte ou des balises autour)."""
    debut = brut.find("{")
    while debut != -1:
        profondeur = 0
        for i in range(debut, len(brut)):
            if brut[i] == "{":
                profondeur += 1
            elif brut[i] == "}":
                profondeur -= 1
                if profondeur == 0:
                    try:
                        return json.loads(brut[debut:i + 1])
                    except json.JSONDecodeError:
                        break
        debut = brut.find("{", debut + 1)
    return None


def executer_agent(fournisseur: FournisseurIA, outils: dict, horloge=time.monotonic) -> Trace:
    """Fait tourner l'agent. `outils` : nom → fonction(arguments: dict) -> str (résultat renvoyé au modèle)."""
    trace = Trace()
    messages = [{"role": "system", "content": CONSIGNE},
                {"role": "user", "content": "Analyse le dossier et propose des pistes d'optimisation."}]
    debut = horloge()
    for tour in range(1, TOURS_MAXIMUM + 1):
        if horloge() - debut > DUREE_MAXIMUM_SECONDES:
            trace.arret = f"durée maximale de {DUREE_MAXIMUM_SECONDES} s atteinte"
            return trace
        try:
            brut = fournisseur.discuter(messages)
        except IAIndisponible as exc:
            trace.arret = str(exc)
            return trace
        action = lire_action(brut)
        messages.append({"role": "assistant", "content": brut})
        if action is None:
            trace.etapes.append(f"tour {tour} : réponse sans JSON valide")
            messages.append({"role": "user", "content": "Réponds par UN objet JSON conforme au protocole."})
            continue
        if action.get("fin"):
            trace.arret = "terminé par l'agent"
            return trace
        nom, arguments = action.get("outil", ""), action.get("arguments") or {}
        if nom not in outils:
            resultat = f"Outil inconnu : {nom}. Outils disponibles : {', '.join(outils)}."
        else:
            try:
                resultat = outils[nom](arguments)
            except Exception as exc:  # un outil mal appelé ne doit pas arrêter l'agent : on lui explique l'erreur
                resultat = f"Erreur de l'outil {nom} : {exc}"
        trace.etapes.append(f"tour {tour} : {nom} — {re.sub(r'\s+', ' ', resultat)[:140]}")
        messages.append({"role": "user", "content": f"Résultat de {nom} :\n{resultat}"})
    trace.arret = f"nombre maximal de {TOURS_MAXIMUM} tours atteint"
    return trace
