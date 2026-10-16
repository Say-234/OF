"""UC14 — Obtenir les propositions de l'agent IA, puis les accepter ou les écarter.

Règle d'or : l'IA propose, le moteur chiffre, l'humain décide. Les garde-fous sont vérifiés ICI,
par le code, et non demandés au modèle :
  - dossier réel + fournisseur non confidentiel → refus (sauf activation explicite par le cabinet) ;
  - article cité inexistant → proposition rejetée ;
  - nombres écrits par l'IA → masqués ; le seul montant affiché est le gain calculé par le moteur ;
  - 10 tours et 90 secondes au plus (boucle.py) ; tout est journalisé, y compris le profil envoyé.
"""
import re
import secrets
from dataclasses import asdict, dataclass, replace
from decimal import Decimal

from optifisc.domaine.erreurs import AccesRefuse, DonneeInvalide, ErreurMetier, IAIndisponible
from optifisc.domaine.moteur.acomptes import echeancier
from optifisc.domaine.moteur.leviers import simuler
from optifisc.domaine.proposition import Proposition
from optifisc.domaine.scenario import LevierChoisi
from optifisc.domaine.utilisateur import Utilisateur

from ..autorisation import exiger
from ..dependances import Dependances
from ..dossiers import ServiceDossiers
from ..ports import FournisseurIA, RechercheArticles
from ..scenarios import ServiceScenarios, effet_du_levier
from .boucle import executer_agent
from .juge import JugeDeterministe
from .outils import construire_outils
from .profil import construire_profil_pseudonymise

NOMBRE = re.compile(r"\d[\d\s.,  ]{3,}\d")      # 5 caractères ou plus : un montant, pas un n° d'article


@dataclass(frozen=True)
class ResultatAgent:
    propositions: tuple[Proposition, ...]
    rejetees: tuple[str, ...]
    etapes: tuple[str, ...]
    arret: str
    modele: str


def masquer_nombres(texte: str) -> str:
    return NOMBRE.sub("[montant masqué]", texte)


def _vers_dict(p: Proposition) -> dict:
    d = asdict(p)
    d["gain"] = None if p.gain is None else str(p.gain)
    d["confiance"] = str(p.confiance)
    return d


def _depuis_dict(d: dict) -> Proposition:
    return Proposition(**{**d, "gain": None if d["gain"] is None else Decimal(d["gain"]),
                          "confiance": Decimal(d["confiance"]), "controles": tuple(d["controles"])})


class ServiceAgent:
    def __init__(self, dep: Dependances, recherche: RechercheArticles, fournisseur: FournisseurIA,
                 autoriser_dossiers_reels: bool = False):
        self.dep = dep
        self.recherche = recherche
        self.fournisseur = fournisseur
        self.autoriser_dossiers_reels = autoriser_dossiers_reels
        self.dossiers = ServiceDossiers(dep)
        self.scenarios = ServiceScenarios(dep)
        self.juge = JugeDeterministe(dep.referentiel, recherche)

    def peut_utiliser_l_ia(self, dossier) -> tuple[bool, str]:
        if not self.fournisseur.disponible:
            return False, "IA désactivée ou non configurée sur ce poste."
        if not dossier.demonstration and not self.fournisseur.confidentiel and not self.autoriser_dossiers_reels:
            return False, ("Dossier réel : l'envoi du profil, même pseudonymisé, à un service d'IA en ligne n'est pas "
                           "autorisé par défaut (doc 01, A.3).")
        return True, ""

    def demander(self, utilisateur: Utilisateur | None, dossier_id: str) -> ResultatAgent:
        dossier = self.dossiers.ouvrir(utilisateur, dossier_id)
        exiger(utilisateur, "demander_propositions", dossier)
        possible, raison = self.peut_utiliser_l_ia(dossier)
        if not possible:
            raise AccesRefuse(raison) if self.fournisseur.disponible else IAIndisponible(raison)
        ref = self.dep.referentiel
        balance = self.dep.balances.derniere(dossier.id)[0]
        resultat = self.dossiers.resultat(dossier)
        ech = echeancier(dossier, resultat, ref, self.dep.horloge.aujourd_hui())
        profil = construire_profil_pseudonymise(dossier, resultat, ech, ref)
        brutes: list[dict] = []
        outils = construire_outils(profil, self.juge, self.recherche, ref, balance, dossier, resultat, brutes)
        trace = executer_agent(self.fournisseur, outils)

        propositions, rejetees = [], []
        for brute in brutes:
            proposition = self._verifier(brute, balance, dossier, resultat)
            if proposition.confiance == 0:
                rejetees.append(f"{proposition.titre} : {proposition.controles[0]}")
            else:
                propositions.append(proposition)
        self.dep.donnees.sauver(dossier.id, "propositions", {
            "liste": [_vers_dict(p) for p in propositions], "rejetees": rejetees, "etapes": trace.etapes,
            "arret": trace.arret, "modele": self.fournisseur.nom})
        profil_envoye = " ; ".join(profil.en_texte().splitlines())
        self.dep.tracer(utilisateur, "appel_ia",
                        f"agent · {self.fournisseur.nom} · {len(propositions)} proposition(s), {len(rejetees)} "
                        f"rejetée(s) · arrêt : {trace.arret} · profil envoyé : {profil_envoye}", dossier.id)
        return ResultatAgent(tuple(propositions), tuple(rejetees), tuple(trace.etapes), trace.arret,
                             self.fournisseur.nom)

    def _verifier(self, brute: dict, balance, dossier, resultat) -> Proposition:
        """Applique les garde-fous à une proposition brute de l'agent."""
        article = "".join(re.findall(r"\d+", str(brute.get("article", ""))))[:4]
        justification = masquer_nombres(str(brute.get("justification", ""))[:600])
        titre = masquer_nombres(str(brute.get("titre", "Proposition"))[:150])
        id_levier = str(brute.get("id_levier") or "")
        parametres = dict(brute.get("parametres") or {})
        gain, bloquant, type_ = None, None, "piste"
        if brute.get("type") == "levier" and id_levier:
            try:
                effet = effet_du_levier(self.dep.referentiel, LevierChoisi(id_levier, parametres), resultat)
                gain = simuler(balance, dossier, self.dep.referentiel, [effet]).gain_is
                bloquant, type_ = effet.bloquant, "levier"
            except (ErreurMetier, ArithmeticError, ValueError, KeyError, TypeError):
                id_levier, parametres = "", {}             # paramètres inutilisables : gardée comme piste
        confiance, controles = self.juge.juger(article, justification, bloquant)
        return Proposition(id=secrets.token_hex(4), type=type_, titre=titre, article=article,
                           justification=justification, id_levier=id_levier if type_ == "levier" else "",
                           parametres=parametres if type_ == "levier" else {}, gain=gain, confiance=confiance,
                           controles=controles)

    def lister(self, utilisateur: Utilisateur | None, dossier_id: str) -> tuple[list[Proposition], dict]:
        self.dossiers.ouvrir(utilisateur, dossier_id)
        donnees = self.dep.donnees.lire(dossier_id, "propositions") or {}
        return [_depuis_dict(d) for d in donnees.get("liste", [])], donnees

    def decider(self, utilisateur: Utilisateur | None, dossier_id: str, proposition_id: str, accepter: bool,
                motif: str = "") -> Proposition:
        dossier = self.dossiers.ouvrir(utilisateur, dossier_id)
        exiger(utilisateur, "preparer_dossier", dossier)
        dossier.verifier_modifiable()
        if not accepter and not motif.strip():
            raise DonneeInvalide("indiquez le motif pour écarter la proposition")
        propositions, donnees = self.lister(utilisateur, dossier_id)
        cible = next((p for p in propositions if p.id == proposition_id), None)
        if cible is None:
            raise DonneeInvalide("proposition introuvable")
        decidee = replace(cible, decision="acceptee" if accepter else "ecartee", motif=motif.strip())
        if accepter and decidee.type == "levier":                 # un levier accepté devient un scénario
            self.scenarios.enregistrer(utilisateur, dossier_id, [LevierChoisi(decidee.id_levier, decidee.parametres)])
        donnees["liste"] = [_vers_dict(decidee if p.id == proposition_id else p) for p in propositions]
        self.dep.donnees.sauver(dossier_id, "propositions", donnees)
        self.dep.tracer(utilisateur, "proposition_" + decidee.decision, f"{decidee.titre} ({decidee.article})"
                        + (f" — motif : {decidee.motif}" if decidee.motif else ""), dossier_id)
        return decidee
