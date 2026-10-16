"""Assemblage de l'application : le SEUL endroit qui connaît toutes les couches (doc 01, B.2).

Il crée les adaptateurs (SQLite, YAML, lecteur de balance, générateur de livrables, IA)
et les donne aux cas d'usage. Pour tester, on appelle construire() avec une base
temporaire et une horloge figée : aucun autre fichier ne change.
"""
import os
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

import yaml
from dotenv import load_dotenv

from optifisc.application.agent.service import ServiceAgent
from optifisc.application.assistant import ServiceAssistant
from optifisc.application.balance import ServiceBalance
from optifisc.application.calcul import ServiceCalcul
from optifisc.application.comptes import ServiceComptes
from optifisc.application.dependances import Dependances
from optifisc.application.dossiers import ServiceDossiers
from optifisc.application.livrables import ServiceLivrables
from optifisc.application.scenarios import ServiceScenarios
from optifisc.application.validation import ServiceValidation
from optifisc.domaine.dossier import Ajustement, CategorieTaux, Hypotheses, Secteur
from optifisc.domaine.utilisateur import Role, Utilisateur
from optifisc.infrastructure.corpus import charger_corpus
from optifisc.infrastructure.horloge import HorlogeSysteme
from optifisc.infrastructure.ia_desactivee import IADesactivee
from optifisc.infrastructure.lecteur_balance import LecteurBalanceTableur
from optifisc.infrastructure.livrables.generateur import GenerateurOffice
from optifisc.infrastructure.openrouter import OpenRouter
from optifisc.infrastructure.persistance.connexion import BaseSqlite
from optifisc.infrastructure.persistance.depots import (
    DepotBalancesSqlite,
    DepotDonneesDossierSqlite,
    DepotDossiersSqlite,
    DepotScenariosSqlite,
    DepotUtilisateursSqlite,
    DepotValidationsSqlite,
    JournalSqlite,
)
from optifisc.infrastructure.recherche_bm25 import RechercheBm25
from optifisc.infrastructure.referentiel_yaml import ReferentielYaml
from optifisc.infrastructure.securite import MotsDePassePbkdf2

RACINE_PROJET = Path(__file__).resolve().parents[2]
MILLESIME = 2026


@dataclass
class Application:
    """Les cas d'usage prêts à l'emploi, tels que l'interface les utilise."""
    dependances: Dependances
    comptes: ServiceComptes
    dossiers: ServiceDossiers
    balance: ServiceBalance
    calcul: ServiceCalcul
    scenarios: ServiceScenarios
    validation: ServiceValidation
    livrables: ServiceLivrables
    assistant: ServiceAssistant
    agent: ServiceAgent
    mode: str = "cabinet"
    aide_demo: str = ""                     # comptes de démonstration affichés sur l'écran de connexion

    @property
    def referentiel(self):
        return self.dependances.referentiel


def fournisseur_ia(usage: str = "ASSISTANT"):
    """Choix du fournisseur d'IA selon .env : OpenRouter (modèles gratuits uniquement) ou aucune IA.

    usage : « ASSISTANT » (rédaction en français à partir d'articles) ou « AGENT » (raisonnement en plusieurs
    étapes) ; chacun peut avoir son modèle (OPENROUTER_MODELE_ASSISTANT / _AGENT), sinon OPENROUTER_MODELE.
    """
    if os.environ.get("OPTIFISC_IA", "desactivee") == "openrouter":
        modele = os.environ.get(f"OPENROUTER_MODELE_{usage}") or os.environ.get("OPENROUTER_MODELE", "")
        return OpenRouter(os.environ.get("OPENROUTER_API_KEY", ""), modele)
    return IADesactivee()


def construire(chemin_base: Path | str | None = None, racine_referentiel: Path | None = None,
               horloge=None, mode: str | None = None, fournisseur=None) -> Application:
    load_dotenv(RACINE_PROJET / ".env")               # réglages locaux (clé d'API…) : jamais dans le code
    mode = mode or os.environ.get("OPTIFISC_MODE", "cabinet")
    chemin_base = chemin_base or os.environ.get("OPTIFISC_BASE") or RACINE_PROJET / "var" / f"optifisc_{mode}.sqlite"
    racine_referentiel = racine_referentiel or RACINE_PROJET / "referentiel"
    horloge = horloge or HorlogeSysteme()
    if mode == "demo":
        Path(chemin_base).unlink(missing_ok=True)       # démonstration : base fictive recréée à chaque démarrage
    base = BaseSqlite(chemin_base)
    dep = Dependances(
        referentiel=ReferentielYaml(racine_referentiel).charger(MILLESIME),
        dossiers=DepotDossiersSqlite(base), balances=DepotBalancesSqlite(base),
        donnees=DepotDonneesDossierSqlite(base), scenarios=DepotScenariosSqlite(base),
        validations=DepotValidationsSqlite(base), journal=JournalSqlite(base),
        lecteur_balance=LecteurBalanceTableur(), horloge=horloge, generateur_livrables=GenerateurOffice(),
    )
    comptes = ServiceComptes(DepotUtilisateursSqlite(base), MotsDePassePbkdf2(), dep.journal, horloge)
    recherche = RechercheBm25(charger_corpus(racine_referentiel / "corpus"))
    ia_assistant = fournisseur or fournisseur_ia("ASSISTANT")
    ia_agent = fournisseur or fournisseur_ia("AGENT")
    reels = os.environ.get("OPTIFISC_IA_DOSSIERS_REELS", "non").lower() == "oui"
    app = Application(dep, comptes, ServiceDossiers(dep), ServiceBalance(dep), ServiceCalcul(dep),
                      ServiceScenarios(dep), ServiceValidation(dep), ServiceLivrables(dep),
                      ServiceAssistant(dep, recherche, ia_assistant), ServiceAgent(dep, recherche, ia_agent, reels),
                      mode)
    if mode == "demo":
        initialiser_demonstration(app, racine_referentiel / "demo")
    return app


# ------------------------------------------------------------------ mode démonstration (doc 06, §4.5)
COMPTES_DEMO = (("admin@demo.bj", "Administrateur (démo)", Role.ADMIN),
                ("expert@demo.bj", "Expert-comptable (démo)", Role.EXPERT),
                ("salim@demo.bj", "Salim A. (démo)", Role.COLLABORATEUR))


def initialiser_demonstration(app: Application, dossier_demo: Path) -> None:
    """Base de démonstration : 3 comptes et 2 dossiers FICTIFS prêts à l'emploi (balance et hypothèses saisies).

    Le mot de passe commun vient de la variable OPTIFISC_MDP_DEMO (secret de l'hébergeur) ; sans elle, il est
    généré au démarrage et affiché sur l'écran de connexion (données fictives uniquement).
    """
    mot_de_passe = os.environ.get("OPTIFISC_MDP_DEMO") or MotsDePassePbkdf2().generer()
    if app.comptes.aucun_compte():                  # toujours vrai : la base de démo vient d'être recréée
        service = MotsDePassePbkdf2()
        for email, nom, role in COMPTES_DEMO:
            app.comptes.utilisateurs.ajouter(Utilisateur(email, nom, role), *service.hacher(mot_de_passe))
        collaborateur = app.comptes.utilisateurs.charger("salim@demo.bj")
        demos = yaml.safe_load((dossier_demo / "demos.yaml").read_text(encoding="utf-8"))["dossiers"]
        for d in demos:
            dossier = app.dossiers.creer(collaborateur, d["raison_sociale"], Secteur(d["secteur"]),
                                         CategorieTaux.DROIT_COMMUN, MILLESIME, demonstration=True)
            contenu = (dossier_demo / d["fichier"]).read_bytes()
            apercu = app.balance.apercu(collaborateur, dossier.id, contenu, d["fichier"], date(MILLESIME, 6, 30))
            app.balance.confirmer(collaborateur, dossier.id, apercu)
            app.dossiers.definir_hypotheses(collaborateur, dossier.id, Hypotheses(
                mois_arrete=6, is_n_moins_1=Decimal(d["is_n_moins_1"]), aib_imputable=Decimal(d["aib"]),
                deficits_anterieurs=Decimal(d["deficits"]),
                ajustements=(Ajustement("6813", "Dotations aux amortissements 2026 à passer",
                                        Decimal(d["dotations_a_passer"])),)))
            if d.get("preparer_jusqu_au_calcul"):        # un dossier prêt à montrer leviers, acomptes, livrables
                for ligne in app.calcul.resultat(collaborateur, dossier.id).retraitements:
                    if not ligne.renseignee:
                        app.dossiers.saisir(collaborateur, dossier.id, ligne.id_regle, Decimal(0))
                app.calcul.calculer(collaborateur, dossier.id)
        app.aide_demo = _aide(mot_de_passe)


def _aide(mot_de_passe: str) -> str:
    lignes = "\n".join(f"- `{email}` — {nom}" for email, nom, _ in COMPTES_DEMO)
    return f"{lignes}\n\nMot de passe commun : `{mot_de_passe}`"
