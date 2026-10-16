"""UC01 — import d'une balance en deux temps : aperçu (rien n'est enregistré), puis confirmation."""
from dataclasses import dataclass, replace
from datetime import date

from optifisc.domaine.balance import Balance, Controle, RapportLecture, controler
from optifisc.domaine.dossier import Dossier, EtatDossier
from optifisc.domaine.erreurs import DonneeInvalide
from optifisc.domaine.utilisateur import Utilisateur

from .autorisation import exiger
from .dependances import Dependances
from .dossiers import ServiceDossiers


@dataclass(frozen=True)
class ApercuImport:
    nom_fichier: str
    date_arrete: date
    balance: Balance
    rapport: RapportLecture
    controles: tuple[Controle, ...]


class ServiceBalance:
    def __init__(self, dep: Dependances):
        self.dep = dep
        self.dossiers = ServiceDossiers(dep)

    def apercu(self, utilisateur: Utilisateur | None, dossier_id: str, contenu: bytes, nom_fichier: str,
               date_arrete: date) -> ApercuImport:
        dossier = self.dossiers.ouvrir(utilisateur, dossier_id)
        exiger(utilisateur, "preparer_dossier", dossier)
        if date_arrete.year != dossier.exercice:
            raise DonneeInvalide(f"la date d'arrêté doit être dans l'exercice {dossier.exercice}")
        balance, rapport = self.dep.lecteur_balance.lire(contenu, nom_fichier)
        return ApercuImport(nom_fichier, date_arrete, balance, rapport, tuple(controler(balance, rapport)))

    def confirmer(self, utilisateur: Utilisateur | None, dossier_id: str, apercu: ApercuImport) -> Dossier:
        dossier = self.dossiers.ouvrir(utilisateur, dossier_id)
        exiger(utilisateur, "preparer_dossier", dossier)
        hypotheses = replace(dossier.hypotheses, mois_arrete=apercu.date_arrete.month)
        if dossier.etat is EtatDossier.BROUILLON:
            dossier = replace(dossier.vers(EtatDossier.EN_PREPARATION), hypotheses=hypotheses)
        else:
            dossier = dossier.modifie(hypotheses=hypotheses)        # refuse si le dossier est figé
        self.dep.balances.enregistrer(dossier.id, apercu.balance, apercu.rapport, apercu.date_arrete,
                                      utilisateur.email, self.dep.horloge.maintenant())
        self.dep.dossiers.enregistrer(dossier)
        self.dep.tracer(utilisateur, "balance_importee",
                        f"{apercu.nom_fichier} : {len(apercu.balance.lignes)} comptes, arrêtée au "
                        f"{apercu.date_arrete:%d/%m/%Y}", dossier.id)
        return dossier
