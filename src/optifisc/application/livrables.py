"""UC04 — livrables : note de pilotage (Word), dossier de calcul (Excel), lettre au DGI (Word).

L'application RASSEMBLE les données (résultat, acomptes, scénario retenu, validation) ;
l'infrastructure (port GenerateurLivrables) les met en forme. Version provisoire
(filigrane « PROJET ») pour le collaborateur, définitive pour l'expert après validation.
"""
import hashlib
from dataclasses import dataclass, field
from datetime import date

from optifisc.domaine.balance import Balance, RapportLecture
from optifisc.domaine.dossier import Dossier, EtatDossier
from optifisc.domaine.erreurs import EtapeIncomplete
from optifisc.domaine.moteur.acomptes import Echeancier, date_depot_declaration, echeancier
from optifisc.domaine.moteur.leviers import Simulation, simuler
from optifisc.domaine.referentiel import Referentiel
from optifisc.domaine.resultat import ResultatFiscal
from optifisc.domaine.utilisateur import Utilisateur

from .autorisation import exiger
from .dependances import Dependances
from .dossiers import ServiceDossiers
from .scenarios import ServiceScenarios, effet_du_levier
from .validation import ServiceValidation


@dataclass(frozen=True)
class Recommandation:
    titre: str
    texte: str


@dataclass(frozen=True)
class DonneesLivrables:
    dossier: Dossier
    referentiel: Referentiel
    resultat: ResultatFiscal
    balance_initiale: Balance
    rapport_lecture: RapportLecture
    date_arrete: date
    echeancier: Echeancier
    demande_reduction: bool
    simulation: Simulation | None
    nom_scenario: str
    recommandations: tuple[Recommandation, ...]
    provisoire: bool
    redacteur: str
    date_edition: date
    date_depot: date
    validation: str = ""                          # « Validée par … le … » ou ""
    regles_non_validees: tuple[str, ...] = ()
    pistes_acceptees: tuple[dict, ...] = field(default_factory=tuple)   # propositions de l'agent acceptées (UC14)


@dataclass(frozen=True)
class Livrable:
    nom: str
    contenu: bytes
    type_mime: str


class ServiceLivrables:
    def __init__(self, dep: Dependances):
        self.dep = dep
        self.dossiers = ServiceDossiers(dep)
        self.scenarios = ServiceScenarios(dep)
        self.validation = ServiceValidation(dep)

    def donnees(self, utilisateur: Utilisateur, dossier: Dossier, provisoire: bool) -> DonneesLivrables:
        ref = self.dep.referentiel
        balance, rapport, date_arrete = self.dep.balances.derniere(dossier.id)
        resultat = self.dossiers.resultat(dossier)
        ech = echeancier(dossier, resultat, ref, self.dep.horloge.aujourd_hui())
        decision_acomptes = self.dep.donnees.lire(dossier.id, "acomptes") or {}
        retenu = self.scenarios.scenario_retenu(dossier.id)
        simulation = None
        if retenu:
            effets = [effet_du_levier(ref, c, resultat) for c in retenu.leviers]
            simulation = simuler(balance, dossier, ref, effets)
        fige = self.dep.donnees.lire(dossier.id, "resultat_fige") or {}
        validation = ""
        if not provisoire and fige:
            validation = f"Note validée par {fige['valide_par']} le {fige['valide_le'][:10]}."
        propositions = (self.dep.donnees.lire(dossier.id, "propositions") or {}).get("liste", [])
        return DonneesLivrables(
            dossier=dossier, referentiel=ref, resultat=resultat, balance_initiale=balance, rapport_lecture=rapport,
            date_arrete=date_arrete, echeancier=ech, demande_reduction=bool(decision_acomptes.get("demande")),
            simulation=simulation, nom_scenario=retenu.nom if retenu else "",
            recommandations=tuple(self._recommandations(resultat, ech, simulation, decision_acomptes)),
            provisoire=provisoire, redacteur=utilisateur.nom, date_edition=self.dep.horloge.aujourd_hui(),
            date_depot=date_depot_declaration(dossier, ref), validation=validation,
            regles_non_validees=tuple(self.validation.regles_non_validees_utilisees(resultat)),
            pistes_acceptees=tuple(p for p in propositions if p.get("decision") == "acceptee"),
        )

    @staticmethod
    def _recommandations(resultat, ech, simulation, decision_acomptes) -> list[Recommandation]:
        """Recommandations rédigées par modèles de phrases à partir des chiffres du moteur (sans IA)."""
        recos = []
        if ech.recommandation and decision_acomptes.get("demande"):
            r = ech.recommandation
            nature = "une dispense" if r.dispense else "une réduction"
            recos.append(Recommandation(
                "Demander au DGI " + nature + " des acomptes restants",
                f"Déposer la demande avant le {r.deposer_avant:%d/%m/%Y} (art. 52). Trésorerie préservée : "
                f"{r.tresorerie_preservee:,.0f} FCFA. {r.risque}".replace(",", " ")))
        elif ech.trop_tard:
            recos.append(Recommandation("Imputer l'excédent d'acomptes",
                                        f"Les acomptes dépasseront l'impôt de {ech.credit_impot:,.0f} FCFA : "
                                        "crédit d'impôt à imputer (art. 51-3).".replace(",", " ")))
        if simulation and simulation.gain_is > 0:
            recos.append(Recommandation("Mettre en œuvre le scénario retenu avant la clôture",
                                        f"Économie d'impôt estimée : {simulation.gain_is:,.0f} FCFA. ".replace(",", " ")
                                        + " ".join(simulation.lecture)))
        if resultat.au_minimum:
            recos.append(Recommandation("Privilégier les leviers de trésorerie",
                                        "Le minimum de perception s'applique : réduire le bénéfice ne réduit pas "
                                        "l'impôt de cette année."))
        return recos

    def generer(self, utilisateur: Utilisateur | None, dossier_id: str, definitif: bool) -> list[Livrable]:
        dossier = self.dossiers.ouvrir(utilisateur, dossier_id)
        if definitif:
            exiger(utilisateur, "livrables_definitifs", dossier)
            if dossier.etat not in (EtatDossier.VALIDE, EtatDossier.LIVRE):
                raise EtapeIncomplete("Les livrables définitifs exigent un dossier validé par l'expert-comptable.")
        else:
            exiger(utilisateur, "livrables_provisoires", dossier)
        if self.dep.balances.derniere(dossier.id) is None:
            raise EtapeIncomplete("Importez d'abord la balance.")
        livrables = self.dep.generateur_livrables.generer(self.donnees(utilisateur, dossier, not definitif))
        empreintes = ", ".join(f"{lv.nom} ({hashlib.sha256(lv.contenu).hexdigest()[:12]})" for lv in livrables)
        self.dep.tracer(utilisateur, "livrables_definitifs" if definitif else "livrables_provisoires", empreintes,
                        dossier.id)
        if definitif and dossier.etat is EtatDossier.VALIDE:
            self.dep.dossiers.enregistrer(dossier.vers(EtatDossier.LIVRE))
        return livrables
