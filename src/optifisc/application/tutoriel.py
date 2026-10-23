"""Journal de missions : le tutoriel guidé de chaque rôle (révision du 17/10/2026, doc 04 §7).

Comme dans un jeu vidéo, chaque rôle reçoit une suite de missions ; chaque mission compte des étapes.
La plupart des étapes se cochent TOUTES SEULES en lisant les données (balance importée, dossier calculé…) :
le tutoriel suit le vrai travail au lieu de le simuler. Quelques étapes de lecture (« parcourir la synthèse »)
ne laissent pas de trace : l'utilisateur les marque lui-même comme faites.

Seules ces coches manuelles et le fait d'avoir vu l'accueil du tutoriel sont enregistrés (table preferences).
Le tutoriel peut être recommencé à tout moment.
"""
from dataclasses import dataclass

from optifisc.domaine.dossier import Dossier, EtatDossier
from optifisc.domaine.utilisateur import Role, Utilisateur

from .autorisation import peut
from .dependances import Dependances
from .dossiers import ServiceDossiers

CLE = "tutoriel"
SOUMIS = {EtatDossier.A_VALIDER, EtatDossier.VALIDE, EtatDossier.LIVRE}


@dataclass(frozen=True)
class EtapeMission:
    id: str
    titre: str
    consigne: str                 # ce qu'il faut faire, en une phrase
    faite: bool
    automatique: bool             # True : cochée par l'application ; False : l'utilisateur la coche
    page: str                     # où aller : « dossier », « dossiers », « utilisateurs », « journal »…
    etape_dossier: str = ""       # onglet du dossier concerné (page « dossier » seulement)


@dataclass(frozen=True)
class Mission:
    id: str
    titre: str
    objectif: str
    etapes: tuple[EtapeMission, ...]

    @property
    def faites(self) -> int:
        return sum(e.faite for e in self.etapes)

    @property
    def terminee(self) -> bool:
        return self.faites == len(self.etapes)


@dataclass(frozen=True)
class Tutoriel:
    role: Role
    missions: tuple[Mission, ...]
    dossier: Dossier | None       # le dossier sur lequel les étapes automatiques sont lues
    vu: bool                      # l'accueil du tutoriel a déjà été montré

    @property
    def total(self) -> int:
        return sum(len(m.etapes) for m in self.missions)

    @property
    def faites(self) -> int:
        return sum(m.faites for m in self.missions)

    @property
    def termine(self) -> bool:
        return self.faites == self.total

    @property
    def en_cours(self) -> tuple[Mission, EtapeMission] | None:
        """La prochaine étape à faire : la première non faite, dans l'ordre des missions."""
        for mission in self.missions:
            for etape in mission.etapes:
                if not etape.faite:
                    return mission, etape
        return None


def _e(id_: str, titre: str, consigne: str, page: str, etape_dossier: str = "", auto: bool | None = True):
    """Gabarit d'étape ; « faite » est calculée plus tard. auto=False : étape cochée à la main."""
    return id_, titre, consigne, page, etape_dossier, auto


# Les missions de chaque rôle, dans l'ordre de l'année fiscale (doc 03 : Préparer, Analyser, Décider, Livrer).
MISSIONS: dict[Role, list[tuple[str, str, str, list[tuple]]]] = {
    Role.COLLABORATEUR: [
        ("c1", "Préparer le dossier", "Donner au moteur des données fiables.", [
            _e("balance", "Importer la balance", "Déposez le fichier Excel/CSV au 30/06. OptiFisc contrôle les colonnes, "
               "projette l'année et affiche le rapport de lecture avant confirmation.", "dossier", "balance"),
            _e("hypotheses", "Confirmer les hypothèses", "Vérifiez la méthode de projection et le régime, puis "
               "confirmez.", "dossier", "hypotheses"),
            _e("retraitements", "Compléter les retraitements", "Saisissez les montants que la balance ne donne pas "
               "(ou « néant »).", "dossier", "retraitements"),
        ]),
        ("c2", "Analyser l'impôt", "Comprendre d'où vient l'IS et comment l'alléger légalement.", [
            _e("calcul", "Calculer l'IS prévisionnel", "Lancez le calcul et lisez le passage du résultat comptable "
               "au résultat fiscal.", "dossier", "calcul"),
            _e("leviers", "Étudier les leviers", "Comparez les scénarios d'optimisation (leviers du catalogue). "
               "Demandez des propositions à l'agent IA (analyse pseudonymisée du dossier), puis enregistrez votre décision.", "dossier", "leviers"),
        ]),
        ("c3", "Décider et transmettre", "Préserver la trésorerie et passer la main à l'expert.", [
            _e("acomptes", "Décider des acomptes", "Choisissez de demander ou non une réduction d'acompte au DGI.",
               "dossier", "acomptes"),
            _e("soumettre", "Soumettre à l'expert", "Depuis la synthèse, soumettez le dossier pour validation.",
               "dossier", "synthese"),
        ]),
    ],
    Role.EXPERT: [
        ("e1", "Revoir le dossier", "Se faire une opinion avant de signer.", [
            _e("lire_synthese", "Lire la synthèse", "Parcourez les indicateurs, les points d'attention et "
               "l'historique du dossier soumis.", "dossier", "synthese", auto=False),
            _e("regles", "Valider les règles utilisées", "Dans le référentiel, validez les règles de retraitement "
               "dont vous assumez l'interprétation.", "referentiel"),
        ]),
        ("e2", "Décider", "Engager le cabinet, ou renvoyer avec un motif.", [
            _e("decision", "Valider ou renvoyer", "Depuis la synthèse, validez le dossier ou renvoyez-le avec un "
               "commentaire.", "dossier", "synthese"),
        ]),
        ("e3", "Livrer au client", "Remettre des documents définitifs et traçables.", [
            _e("livrer", "Générer les livrables définitifs", "Produisez la note de synthèse (Word) et le classeur "
               "(Excel).", "dossier", "livrer"),
        ]),
    ],
    Role.ADMIN: [
        ("a1", "Organiser l'équipe", "Chacun accède à ses dossiers, et seulement à eux.", [
            _e("utilisateur", "Créer un compte", "Ajoutez un collaborateur ou un expert ; transmettez-lui son mot "
               "de passe initial.", "utilisateurs"),
            _e("attribuer", "Attribuer un dossier", "Confiez un dossier à un collaborateur.", "utilisateurs"),
        ]),
        ("a2", "Garder la trace", "Savoir qui a fait quoi, et quand.", [
            _e("journal", "Consulter le journal d'audit", "Filtrez le journal par dossier ou par action.", "journal",
               auto=False),
            _e("referentiel", "Parcourir le référentiel", "Voyez les règles en vigueur et leur statut de "
               "validation.", "referentiel", auto=False),
        ]),
    ],
}


class ServiceTutoriel:
    def __init__(self, dep: Dependances):
        self.dep = dep

    # ------------------------------------------------------------------ lecture
    def tutoriel(self, utilisateur: Utilisateur, dossier_id: str | None = None) -> Tutoriel:
        prefs = self._lire(utilisateur)
        dossier = self._dossier_de_reference(utilisateur, dossier_id)
        constats = self._constats(utilisateur, dossier)
        missions = []
        for id_m, titre, objectif, gabarits in MISSIONS[utilisateur.role]:
            etapes = tuple(
                EtapeMission(id_, t, consigne, constats.get(id_, False) if auto else id_ in prefs["faites"],
                             bool(auto), page, onglet)
                for id_, t, consigne, page, onglet, auto in gabarits)
            missions.append(Mission(id_m, titre, objectif, etapes))
        return Tutoriel(utilisateur.role, tuple(missions), dossier, prefs["vu"])

    # ------------------------------------------------------------------ écriture (préférences seulement)
    def cocher(self, utilisateur: Utilisateur, etape_id: str, faite: bool = True) -> None:
        prefs = self._lire(utilisateur)
        faites = set(prefs["faites"])
        faites.add(etape_id) if faite else faites.discard(etape_id)
        self._sauver(utilisateur, faites=sorted(faites), vu=prefs["vu"])

    def marquer_vu(self, utilisateur: Utilisateur) -> None:
        self._sauver(utilisateur, faites=self._lire(utilisateur)["faites"], vu=True)

    def recommencer(self, utilisateur: Utilisateur) -> None:
        """Efface les coches manuelles et remontre l'accueil. Les étapes automatiques reflètent les données."""
        self._sauver(utilisateur, faites=[], vu=False)

    # ------------------------------------------------------------------ interne
    def _lire(self, utilisateur: Utilisateur) -> dict:
        lu = self.dep.preferences.lire(utilisateur.email, CLE) if self.dep.preferences else None
        return {"faites": list((lu or {}).get("faites", [])), "vu": bool((lu or {}).get("vu", False))}

    def _sauver(self, utilisateur: Utilisateur, **valeur) -> None:
        if self.dep.preferences:
            self.dep.preferences.sauver(utilisateur.email, CLE, valeur)

    def _dossier_de_reference(self, utilisateur: Utilisateur, dossier_id: str | None) -> Dossier | None:
        """Le dossier ouvert s'il y en a un ; sinon le plus pertinent pour le rôle parmi ceux qu'il voit."""
        visibles = [d for d in self.dep.dossiers.lister() if peut(utilisateur, "voir_dossier", d)]
        if dossier_id:
            ouvert = next((d for d in visibles if d.id == dossier_id), None)
            if ouvert:
                return ouvert
        if utilisateur.role is Role.COLLABORATEUR:
            visibles = [d for d in visibles if d.responsable == utilisateur.email] or visibles
        # l'expert d'abord sur ce qu'il doit valider ; sinon le dossier non livré le plus avancé
        priorite = {EtatDossier.A_VALIDER: 0} if utilisateur.role is Role.EXPERT else {}
        rang = list(EtatDossier)
        visibles.sort(key=lambda d: (priorite.get(d.etat, 1), d.etat is EtatDossier.LIVRE, -rang.index(d.etat),
                                     d.raison_sociale))
        return visibles[0] if visibles else None

    def _constats(self, utilisateur: Utilisateur, dossier: Dossier | None) -> dict[str, bool]:
        """Ce que les données prouvent déjà. Les actions du journal sont celles de CET utilisateur."""
        evenements = self.dep.journal.lister(None, 1000)
        mes_actions = {e.action for e in evenements if e.utilisateur == utilisateur.email}
        constats = {
            "regles": bool(self.dep.validations.lister()),
            "utilisateur": "utilisateur_cree" in mes_actions,
            "attribuer": "dossier_attribue" in mes_actions,
        }
        if dossier is None:
            return constats
        # les étapes du dossier (balance, hypothèses, retraitements, calcul, leviers, acomptes, livrer) : même
        # règle que les coches des onglets du dossier, pour que tutoriel et dossier ne se contredisent jamais
        constats.update({e.id: e.faite for e in ServiceDossiers(self.dep).etapes(dossier)})
        renvoye = any(e.action == "dossier_renvoye" and e.dossier_id == dossier.id for e in evenements)
        constats["soumettre"] = dossier.etat in SOUMIS
        constats["decision"] = dossier.etat in {EtatDossier.VALIDE, EtatDossier.LIVRE} or renvoye
        return constats
