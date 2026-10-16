"""UC03 — simuler des leviers, enregistrer jusqu'à 3 scénarios, en retenir un (ou aucun)."""
import secrets
from decimal import Decimal

from optifisc.domaine.dossier import Dossier
from optifisc.domaine.erreurs import DonneeInvalide
from optifisc.domaine.montant import en_texte
from optifisc.domaine.moteur import leviers as L
from optifisc.domaine.referentiel import Referentiel
from optifisc.domaine.resultat import ResultatFiscal
from optifisc.domaine.scenario import NOMBRE_MAXIMUM_DE_SCENARIOS, LevierChoisi, Scenario
from optifisc.domaine.utilisateur import Utilisateur

from .autorisation import exiger
from .dependances import Dependances
from .dossiers import ServiceDossiers


def _oui(valeur) -> bool:
    return valeur in (True, "True", "true", "oui", 1, "1")


def effet_du_levier(ref: Referentiel, choix: LevierChoisi, resultat: ResultatFiscal) -> L.EffetLevier:
    """Transforme les paramètres saisis à l'écran en effet chiffré par le moteur."""
    p = choix.parametres
    montant = Decimal(str(p.get("montant", p.get("montant_ht", "0"))))
    if choix.id_levier == "L01_INVESTISSEMENT_DEGRESSIF":
        return L.investissement_degressif(ref, montant, int(p["duree"]), int(p["mois_acquisition"]),
                                          _oui(p.get("neuf", True)))
    if choix.id_levier == "L02_AMORTISSEMENT_ACCELERE":
        return L.investissement_accelere(ref, montant, int(p["duree"]), int(p["mois_acquisition"]),
                                         _oui(p.get("neuf", True)), _oui(p.get("usage_exclusif", True)))
    if choix.id_levier == "L03_PROVISION_JUSTIFIEE":
        return L.provision(ref, montant, _oui(p.get("justifiee")), _oui(p.get("au_releve")))
    if choix.id_levier == "L04_DONS_PLAFOND":
        deja = L.dons_deja_comptabilises(ref, resultat.balance_projetee)
        return L.dons(ref, montant, deja, resultat.chiffre_affaires, _oui(p.get("vers_etat")))
    if choix.id_levier == "L05_CHARGES_ANTICIPEES":
        return L.charges_anticipees(ref, montant, str(p.get("nature", "Charge anticipée")), _oui(p.get("especes")))
    raise DonneeInvalide(f"levier non simulable : {choix.id_levier}")


class ServiceScenarios:
    def __init__(self, dep: Dependances):
        self.dep = dep
        self.dossiers = ServiceDossiers(dep)

    def _preparer(self, utilisateur, dossier_id) -> Dossier:
        dossier = self.dossiers.ouvrir(utilisateur, dossier_id)
        exiger(utilisateur, "preparer_dossier", dossier)
        return dossier

    def simuler(self, utilisateur: Utilisateur | None, dossier_id: str, choix: list[LevierChoisi]) -> L.Simulation:
        dossier = self._preparer(utilisateur, dossier_id)
        resultat = self.dossiers.resultat(dossier)
        effets = [effet_du_levier(self.dep.referentiel, c, resultat) for c in choix]
        balance = self.dep.balances.derniere(dossier.id)[0]
        return L.simuler(balance, dossier, self.dep.referentiel, effets)

    def effets(self, utilisateur: Utilisateur | None, dossier_id: str, choix: list[LevierChoisi]):
        dossier = self._preparer(utilisateur, dossier_id)
        resultat = self.dossiers.resultat(dossier)
        return [effet_du_levier(self.dep.referentiel, c, resultat) for c in choix]

    def lister(self, utilisateur: Utilisateur | None, dossier_id: str) -> list[Scenario]:
        self.dossiers.ouvrir(utilisateur, dossier_id)
        return self.dep.scenarios.lister(dossier_id)

    def enregistrer(self, utilisateur: Utilisateur | None, dossier_id: str, choix: list[LevierChoisi]) -> Scenario:
        dossier = self._preparer(utilisateur, dossier_id)
        dossier.verifier_modifiable()
        existants = self.dep.scenarios.lister(dossier_id)
        if len(existants) >= NOMBRE_MAXIMUM_DE_SCENARIOS:
            raise DonneeInvalide(f"{NOMBRE_MAXIMUM_DE_SCENARIOS} scénarios au plus : supprimez-en un d'abord")
        if not choix:
            raise DonneeInvalide("choisissez au moins un levier")
        noms_pris = {s.nom for s in existants}
        nom = next(n for n in "ABC" if n not in noms_pris)
        simulation = self.simuler(utilisateur, dossier_id, choix)
        scenario = Scenario(f"{dossier_id}-{secrets.token_hex(3)}", dossier_id, nom, tuple(choix), simulation.gain_is)
        self.dep.scenarios.enregistrer(scenario)
        leviers = ", ".join(c.id_levier for c in choix)
        self.dep.tracer(utilisateur, "scenario_enregistre",
                        f"scénario {nom} : {leviers} ; gain {en_texte(simulation.gain_is)}", dossier_id)
        return scenario

    def supprimer(self, utilisateur: Utilisateur | None, dossier_id: str, scenario_id: str) -> None:
        self._preparer(utilisateur, dossier_id).verifier_modifiable()
        self.dep.scenarios.supprimer(scenario_id)
        self.dep.tracer(utilisateur, "scenario_supprime", scenario_id, dossier_id)

    def retenir(self, utilisateur: Utilisateur | None, dossier_id: str, scenario_id: str | None) -> None:
        """Retient un scénario pour la note, ou aucun (None) : dans les deux cas la décision est enregistrée."""
        self._preparer(utilisateur, dossier_id).verifier_modifiable()
        retenu = None
        for s in self.dep.scenarios.lister(dossier_id):
            est_retenu = s.id == scenario_id
            if est_retenu:
                retenu = s
            if s.retenu != est_retenu:
                self.dep.scenarios.enregistrer(Scenario(s.id, s.dossier_id, s.nom, s.leviers, s.gain_is, est_retenu))
        if scenario_id is not None and retenu is None:
            raise DonneeInvalide("scénario introuvable")
        self.dep.donnees.sauver(dossier_id, "decision_leviers",
                                {"scenario_id": scenario_id or "", "nom": retenu.nom if retenu else "",
                                 "par": utilisateur.email})
        self.dep.tracer(utilisateur, "decision_leviers",
                        f"scénario {retenu.nom} retenu" if retenu else "aucun levier retenu", dossier_id)

    def scenario_retenu(self, dossier_id: str) -> Scenario | None:
        return next((s for s in self.dep.scenarios.lister(dossier_id) if s.retenu), None)
