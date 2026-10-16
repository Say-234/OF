"""UC07 — calcul de l'IS prévisionnel ; UC08 — acomptes et décision de demande de réduction."""
from decimal import Decimal

from optifisc.domaine.dossier import Dossier, EtatDossier
from optifisc.domaine.moteur.acomptes import Echeancier, echeancier
from optifisc.domaine.resultat import ResultatFiscal
from optifisc.domaine.utilisateur import Utilisateur

from .autorisation import exiger
from .dependances import Dependances
from .dossiers import ServiceDossiers


class ServiceCalcul:
    def __init__(self, dep: Dependances):
        self.dep = dep
        self.dossiers = ServiceDossiers(dep)

    def resultat(self, utilisateur: Utilisateur | None, dossier_id: str) -> ResultatFiscal:
        """Consultation : recalcule à partir des données enregistrées, sans changer l'état."""
        return self.dossiers.resultat(self.dossiers.ouvrir(utilisateur, dossier_id))

    def calculer(self, utilisateur: Utilisateur | None, dossier_id: str) -> ResultatFiscal:
        dossier = self.dossiers.ouvrir(utilisateur, dossier_id)
        exiger(utilisateur, "preparer_dossier", dossier)
        resultat = self.dossiers.resultat(dossier)
        if dossier.etat is EtatDossier.EN_PREPARATION:
            dossier = dossier.vers(EtatDossier.CALCULE)
            self.dep.dossiers.enregistrer(dossier)
        self._mettre_a_jour_resume(dossier, resultat)
        self.dep.tracer(utilisateur, "calcul_effectue",
                        f"IS dû {resultat.is_du} FCFA ({resultat.regime}), résultat fiscal {resultat.resultat_fiscal}",
                        dossier.id)
        return resultat

    def echeancier(self, utilisateur: Utilisateur | None, dossier_id: str, marge: Decimal | None = None) -> Echeancier:
        dossier = self.dossiers.ouvrir(utilisateur, dossier_id)
        resultat = self.dossiers.resultat(dossier)
        return echeancier(dossier, resultat, self.dep.referentiel, self.dep.horloge.aujourd_hui(), marge)

    def decider_acomptes(self, utilisateur: Utilisateur | None, dossier_id: str, demander: bool,
                         marge: Decimal | None = None) -> Echeancier:
        dossier = self.dossiers.ouvrir(utilisateur, dossier_id)
        exiger(utilisateur, "preparer_dossier", dossier)
        dossier.verifier_modifiable()
        ech = self.echeancier(utilisateur, dossier_id, marge)
        reco = ech.recommandation if demander else None
        self.dep.donnees.sauver(dossier.id, "acomptes", {
            "demande": bool(reco), "marge": str(reco.marge) if reco else "",
            "acompte_demande": str(reco.acompte_demande) if reco else "",
            "deposer_avant": reco.deposer_avant.isoformat() if reco else "", "par": utilisateur.email})
        self._mettre_a_jour_resume(dossier, self.dossiers.resultat(dossier))
        self.dep.tracer(utilisateur, "decision_acomptes",
                        f"demande de réduction : {'oui' if reco else 'non'}", dossier.id)
        return ech

    def _mettre_a_jour_resume(self, dossier: Dossier, resultat: ResultatFiscal) -> None:
        """Résumé pour le tableau de bord (évite de recalculer 30 dossiers pour afficher une liste)."""
        ech = echeancier(dossier, resultat, self.dep.referentiel, self.dep.horloge.aujourd_hui())
        prochaine = ""
        if ech.recommandation:
            prochaine = f"Réduction d'acompte : déposer avant le {ech.recommandation.deposer_avant:%d/%m/%Y}"
        elif ech.trop_tard:
            prochaine = "Excédent d'acomptes : crédit d'impôt à imputer"
        self.dep.donnees.sauver(dossier.id, "resume", {"is_du": str(resultat.is_du), "regime": resultat.regime,
                                                       "prochaine_echeance": prochaine})
