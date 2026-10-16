"""Cas d'usage des dossiers : création et liste (UC05), hypothèses (UC06), saisies, étapes du parcours."""
import re
import secrets
from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal

from optifisc.domaine.dossier import CategorieTaux, Dossier, EtatDossier, Hypotheses, Secteur
from optifisc.domaine.erreurs import DonneeInvalide, EtapeIncomplete
from optifisc.domaine.montant import en_texte
from optifisc.domaine.moteur.impot import calculer_is
from optifisc.domaine.resultat import ResultatFiscal
from optifisc.domaine.utilisateur import Role, Utilisateur

from .autorisation import exiger, peut
from .dependances import Dependances

ETAPES = (("balance", "Balance"), ("hypotheses", "Hypothèses"), ("retraitements", "Retraitements"),
          ("calcul", "Calcul"), ("leviers", "Leviers"), ("acomptes", "Acomptes"), ("livrer", "Livrer"))
ETATS_CALCULES = {EtatDossier.CALCULE, EtatDossier.A_VALIDER, EtatDossier.VALIDE, EtatDossier.LIVRE}


@dataclass(frozen=True)
class Etape:
    id: str
    numero: int
    libelle: str
    faite: bool
    accessible: bool
    raison: str = ""                     # pourquoi l'étape n'est pas accessible


@dataclass(frozen=True)
class ResumeDossier:
    """Ce que le tableau de bord affiche, sans charger le dossier complet."""
    dossier: Dossier
    date_arrete: date | None
    is_du: Decimal | None
    regime: str
    prochaine_echeance: str
    etapes_faites: int


class ServiceDossiers:
    def __init__(self, dep: Dependances):
        self.dep = dep

    # ------------------------------------------------------------------ lecture
    def ouvrir(self, utilisateur: Utilisateur | None, dossier_id: str) -> Dossier:
        dossier = self.dep.dossiers.charger(dossier_id)
        if dossier is None:
            raise DonneeInvalide(f"dossier introuvable : {dossier_id}")
        exiger(utilisateur, "voir_dossier", dossier)
        return dossier

    def lister(self, utilisateur: Utilisateur | None) -> list[ResumeDossier]:
        visibles = [d for d in self.dep.dossiers.lister() if peut(utilisateur, "voir_dossier", d)]
        resumes = []
        for d in visibles:
            resume = self.dep.donnees.lire(d.id, "resume") or {}
            balance = self.dep.balances.derniere(d.id)
            resumes.append(ResumeDossier(
                dossier=d, date_arrete=balance[2] if balance else None,
                is_du=Decimal(resume["is_du"]) if "is_du" in resume else None, regime=resume.get("regime", ""),
                prochaine_echeance=resume.get("prochaine_echeance", ""),
                etapes_faites=sum(e.faite for e in self.etapes(d))))
        # urgent d'abord : « à valider » en tête pour l'expert, puis par nom
        return sorted(resumes, key=lambda r: (r.dossier.etat is not EtatDossier.A_VALIDER, r.dossier.raison_sociale))

    def resultat(self, dossier: Dossier) -> ResultatFiscal:
        """Recalcule l'IS à partir des données enregistrées (calcul pur et rapide : rien n'est gardé en mémoire)."""
        balance = self.dep.balances.derniere(dossier.id)
        if balance is None:
            raise EtapeIncomplete("Importez d'abord la balance (étape 1).")
        return calculer_is(balance[0], dossier, self.dep.referentiel)

    def etapes(self, dossier: Dossier) -> list[Etape]:
        a_balance = self.dep.balances.derniere(dossier.id) is not None
        hypotheses = self.dep.donnees.lire(dossier.id, "hypotheses_confirmees") is not None
        saisies_ok = a_balance and not self.resultat(dossier).saisies_manquantes
        calcule = dossier.etat in ETATS_CALCULES
        faites = {
            "balance": a_balance, "hypotheses": hypotheses, "retraitements": saisies_ok and hypotheses,
            "calcul": calcule, "leviers": self.dep.donnees.lire(dossier.id, "decision_leviers") is not None,
            "acomptes": self.dep.donnees.lire(dossier.id, "acomptes") is not None,
            "livrer": dossier.etat is EtatDossier.LIVRE,
        }
        accessibles = {
            "balance": (True, ""), "hypotheses": (a_balance, "Importez d'abord la balance."),
            "retraitements": (a_balance, "Importez d'abord la balance."),
            "calcul": (a_balance, "Importez d'abord la balance."),
            "leviers": (calcule, "Calculez d'abord l'impôt."), "acomptes": (calcule, "Calculez d'abord l'impôt."),
            "livrer": (calcule, "Calculez d'abord l'impôt."),
        }
        return [Etape(id_, n, libelle, faites[id_], *accessibles[id_]) for n, (id_, libelle) in enumerate(ETAPES, 1)]

    # ------------------------------------------------------------------ UC05 création
    def creer(self, utilisateur: Utilisateur | None, raison_sociale: str, secteur: Secteur,
              categorie_taux: CategorieTaux, exercice: int, demonstration: bool = False,
              responsable: str = "") -> Dossier:
        exiger(utilisateur, "creer_dossier")
        if not raison_sociale.strip():
            raise DonneeInvalide("la raison sociale est obligatoire")
        if exercice != self.dep.referentiel.millesime:
            raise DonneeInvalide(f"seul l'exercice {self.dep.referentiel.millesime} est couvert par le référentiel")
        if utilisateur.role is Role.COLLABORATEUR or not responsable:
            responsable = utilisateur.email                      # un collaborateur crée ses propres dossiers
        identifiant = f"{re.sub(r'[^a-z0-9]+', '-', raison_sociale.lower()).strip('-')[:30]}-{secrets.token_hex(3)}"
        dossier = Dossier(id=identifiant, raison_sociale=raison_sociale.strip(), secteur=secteur,
                          categorie_taux=categorie_taux, exercice=exercice, demonstration=demonstration,
                          responsable=responsable)
        self.dep.dossiers.enregistrer(dossier)
        self.dep.tracer(utilisateur, "dossier_cree", raison_sociale, dossier.id)
        return dossier

    def modifier_identite(self, utilisateur, dossier_id: str, secteur: Secteur, categorie_taux: CategorieTaux):
        dossier = self.ouvrir(utilisateur, dossier_id)
        exiger(utilisateur, "preparer_dossier", dossier)
        dossier = dossier.modifie(secteur=secteur, categorie_taux=categorie_taux)
        self.dep.dossiers.enregistrer(dossier)
        self.dep.tracer(utilisateur, "identite_modifiee", f"{secteur.value}, {categorie_taux.value}", dossier.id)
        return dossier

    # ------------------------------------------------------------------ UC06 hypothèses
    def definir_hypotheses(self, utilisateur: Utilisateur | None, dossier_id: str, hypotheses: Hypotheses) -> Dossier:
        dossier = self.ouvrir(utilisateur, dossier_id)
        exiger(utilisateur, "preparer_dossier", dossier)
        dossier = dossier.modifie(hypotheses=hypotheses)
        self.dep.dossiers.enregistrer(dossier)
        self.dep.donnees.sauver(dossier.id, "hypotheses_confirmees", {"par": utilisateur.email})
        self.dep.tracer(utilisateur, "hypotheses_definies",
                        f"arrêté à fin de mois {hypotheses.mois_arrete}, coefficient {hypotheses.coef_activite}, "
                        f"{len(hypotheses.ajustements)} ajustement(s)", dossier.id)
        return dossier

    # ------------------------------------------------------------------ UC02 saisies
    def saisir(self, utilisateur: Utilisateur | None, dossier_id: str, id_regle: str,
               montant: Decimal | None) -> Dossier:
        """Montant saisi pour une règle « à saisie ». 0 = néant ; None = retirer la réponse (non renseigné)."""
        dossier = self.ouvrir(utilisateur, dossier_id)
        exiger(utilisateur, "preparer_dossier", dossier)
        ref = self.dep.referentiel
        ids = {r.id for r in ref.regles if r.est_saisie} | {s.id for s in ref.sanctions}
        if id_regle not in ids:
            raise DonneeInvalide(f"règle sans saisie : {id_regle}")
        if montant is not None and montant < 0:
            raise DonneeInvalide("un montant saisi ne peut pas être négatif")
        saisies = dict(dossier.saisies)
        if montant is None:
            saisies.pop(id_regle, None)
        else:
            saisies[id_regle] = montant
        dossier = dossier.modifie(saisies=saisies)
        self.dep.dossiers.enregistrer(dossier)
        texte = "non renseigné" if montant is None else ("néant" if montant == 0 else en_texte(montant))
        self.dep.tracer(utilisateur, "saisie", f"{id_regle} : {texte}", dossier.id)
        return dossier

    def journal(self, utilisateur: Utilisateur | None, dossier_id: str | None = None, limite: int = 200) -> list:
        """UC11 : chronologie des événements ; un collaborateur ne voit que ceux de ses dossiers."""
        if dossier_id:
            dossier = self.ouvrir(utilisateur, dossier_id)
            exiger(utilisateur, "consulter_journal", dossier)
            return self.dep.journal.lister(dossier_id, limite)
        exiger(utilisateur, "consulter_journal")
        evenements = self.dep.journal.lister(None, limite)
        if utilisateur.role is Role.COLLABORATEUR:
            siens = {d.id for d in self.dep.dossiers.lister() if d.responsable == utilisateur.email}
            evenements = [e for e in evenements if e.dossier_id in siens or e.utilisateur == utilisateur.email]
        return evenements

    def attribuer(self, utilisateur: Utilisateur | None, dossier_id: str, email: str) -> Dossier:
        exiger(utilisateur, "attribuer_dossier")
        dossier = self.dep.dossiers.charger(dossier_id)
        if dossier is None:
            raise DonneeInvalide(f"dossier introuvable : {dossier_id}")
        dossier = replace(dossier, responsable=email)
        self.dep.dossiers.enregistrer(dossier)
        self.dep.tracer(utilisateur, "dossier_attribue", f"à {email}", dossier.id)
        return dossier
