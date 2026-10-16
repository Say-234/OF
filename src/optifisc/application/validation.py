"""UC04 — soumettre, valider, renvoyer, rouvrir un dossier ; UC10 — valider une règle du référentiel."""
import hashlib
from dataclasses import dataclass

from optifisc.domaine.dossier import Dossier, EtatDossier
from optifisc.domaine.erreurs import DonneeInvalide, EtapeIncomplete
from optifisc.domaine.montant import en_texte
from optifisc.domaine.referentiel import RegleRetraitement, Statut
from optifisc.domaine.resultat import ResultatFiscal
from optifisc.domaine.utilisateur import Utilisateur

from .autorisation import exiger
from .dependances import Dependances
from .dossiers import ServiceDossiers


@dataclass(frozen=True)
class PointDeControle:
    libelle: str
    respecte: bool


def empreinte_regle(regle: RegleRetraitement) -> str:
    """Empreinte du contenu d'une règle : si la règle change dans le YAML, sa validation devient caduque."""
    return hashlib.sha256(repr(regle).encode()).hexdigest()[:12]


class ServiceValidation:
    def __init__(self, dep: Dependances):
        self.dep = dep
        self.dossiers = ServiceDossiers(dep)

    # ------------------------------------------------------------------ statut effectif des règles (UC10)
    def regles_validees(self) -> dict[str, dict]:
        """Règles validées par le cabinet, et dont le contenu n'a pas changé depuis la validation."""
        validations = self.dep.validations.lister()
        resultat = {}
        for regle in self.dep.referentiel.regles:
            v = validations.get(regle.id)
            if regle.statut is Statut.VALIDE:
                resultat[regle.id] = {"valide_par": "référentiel", "quand": None, "cas": "", "commentaire": ""}
            elif v and v["version"] == empreinte_regle(regle):
                resultat[regle.id] = v
        return resultat

    def regles_non_validees_utilisees(self, resultat: ResultatFiscal) -> list[str]:
        validees = self.regles_validees()
        return [li.id_regle for li in resultat.retraitements if li.montant > 0 and li.id_regle not in validees]

    def valider_regle(self, utilisateur: Utilisateur | None, id_regle: str, cas: str, commentaire: str = "") -> None:
        exiger(utilisateur, "valider_regle")
        regle = self.dep.referentiel.regle(id_regle)
        if not cas.strip():
            raise DonneeInvalide("décrivez le cas chiffré sur lequel la règle a été vérifiée")
        self.dep.validations.valider(id_regle, empreinte_regle(regle), utilisateur.email, cas, commentaire,
                                     self.dep.horloge.maintenant())
        self.dep.tracer(utilisateur, "regle_validee", f"{id_regle} sur le cas « {cas} »")

    def remettre_a_valider(self, utilisateur: Utilisateur | None, id_regle: str) -> None:
        exiger(utilisateur, "valider_regle")
        self.dep.validations.annuler(id_regle)
        self.dep.tracer(utilisateur, "regle_remise_a_valider", id_regle)

    # ------------------------------------------------------------------ UC04 cycle de validation du dossier
    def liste_de_controle(self, dossier: Dossier) -> list[PointDeControle]:
        """Doc 04, §3 : ce qui doit être vrai avant de soumettre."""
        a_balance = self.dep.balances.derniere(dossier.id) is not None
        resultat = self.dossiers.resultat(dossier) if a_balance else None
        return [
            PointDeControle("Balance importée et contrôlée", a_balance),
            PointDeControle("Hypothèses de projection renseignées",
                            self.dep.donnees.lire(dossier.id, "hypotheses_confirmees") is not None),
            PointDeControle("Aucune règle de retraitement « non renseignée »",
                            resultat is not None and not resultat.saisies_manquantes),
            PointDeControle("Calcul à jour (aucune donnée modifiée depuis)", dossier.etat is EtatDossier.CALCULE),
            PointDeControle("Décision sur les acomptes enregistrée (y compris « pas de demande »)",
                            self.dep.donnees.lire(dossier.id, "acomptes") is not None),
        ]

    def soumettre(self, utilisateur: Utilisateur | None, dossier_id: str) -> Dossier:
        dossier = self.dossiers.ouvrir(utilisateur, dossier_id)
        exiger(utilisateur, "soumettre_dossier", dossier)
        manquants = [p.libelle for p in self.liste_de_controle(dossier) if not p.respecte]
        if manquants:
            raise EtapeIncomplete("Avant de soumettre : " + " ; ".join(manquants) + ".")
        dossier = dossier.vers(EtatDossier.A_VALIDER)
        self.dep.dossiers.enregistrer(dossier)
        self.dep.donnees.sauver(dossier.id, "soumission", {"par": utilisateur.email,
                                                         "quand": self.dep.horloge.maintenant().isoformat()})
        self.dep.tracer(utilisateur, "dossier_soumis", "soumis à la validation de l'expert-comptable", dossier.id)
        return dossier

    def valider(self, utilisateur: Utilisateur | None, dossier_id: str,
                regles_non_validees_verifiees: bool = False) -> Dossier:
        dossier = self.dossiers.ouvrir(utilisateur, dossier_id)
        exiger(utilisateur, "valider_dossier", dossier)
        if dossier.etat is not EtatDossier.A_VALIDER:
            raise EtapeIncomplete("Seul un dossier « à valider » peut être validé.")
        resultat = self.dossiers.resultat(dossier)
        non_validees = self.regles_non_validees_utilisees(resultat)
        if non_validees and not regles_non_validees_verifiees:
            raise EtapeIncomplete(f"{len(non_validees)} règle(s) non validée(s) par le cabinet sont utilisées "
                                  f"({', '.join(non_validees)}) : cochez « J'ai vérifié les règles non validées ».")
        soumission = self.dep.donnees.lire(dossier.id, "soumission") or {}
        meme_personne = soumission.get("par") == utilisateur.email
        self.dep.donnees.sauver(dossier.id, "resultat_fige", {
            "is_du": str(resultat.is_du), "impot_total": str(resultat.impot_total),
            "resultat_fiscal": str(resultat.resultat_fiscal), "resultat_comptable": str(resultat.resultat_comptable),
            "regime": resultat.regime, "version_referentiel": resultat.version_referentiel,
            "valide_par": utilisateur.email, "valide_le": self.dep.horloge.maintenant().isoformat(),
            "prepare_par": soumission.get("par", ""), "meme_personne": meme_personne,
            "regles_non_validees": non_validees,
            "audit": [[a.etape, a.reference, a.libelle, a.article, str(a.base), str(a.montant), a.detail]
                      for a in resultat.audit],
        })
        dossier = dossier.vers(EtatDossier.VALIDE)
        self.dep.dossiers.enregistrer(dossier)
        mention = " (préparé et validé par la même personne)" if meme_personne else ""
        self.dep.tracer(utilisateur, "dossier_valide", f"IS dû {en_texte(resultat.is_du)}{mention}", dossier.id)
        return dossier

    def renvoyer(self, utilisateur: Utilisateur | None, dossier_id: str, commentaire: str) -> Dossier:
        dossier = self.dossiers.ouvrir(utilisateur, dossier_id)
        exiger(utilisateur, "valider_dossier", dossier)
        if not commentaire.strip():
            raise DonneeInvalide("un commentaire est obligatoire pour renvoyer le dossier")
        dossier = dossier.vers(EtatDossier.EN_PREPARATION)
        self.dep.dossiers.enregistrer(dossier)
        self.dep.donnees.sauver(dossier.id, "renvoi", {"par": utilisateur.email, "commentaire": commentaire})
        self.dep.tracer(utilisateur, "dossier_renvoye", commentaire, dossier.id)
        return dossier

    def rouvrir(self, utilisateur: Utilisateur | None, dossier_id: str, motif: str) -> Dossier:
        dossier = self.dossiers.ouvrir(utilisateur, dossier_id)
        exiger(utilisateur, "rouvrir_dossier", dossier)
        if dossier.etat not in (EtatDossier.VALIDE, EtatDossier.LIVRE):
            raise EtapeIncomplete("Seul un dossier validé ou livré peut être rouvert.")
        if not motif.strip():
            raise DonneeInvalide("le motif de réouverture est obligatoire")
        dossier = dossier.vers(EtatDossier.EN_PREPARATION)
        self.dep.dossiers.enregistrer(dossier)
        self.dep.tracer(utilisateur, "dossier_rouvert", motif, dossier.id)
        return dossier
