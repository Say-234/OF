"""Cas d'usage des comptes : connexion (UC12), utilisateurs et attributions (UC13)."""
from dataclasses import replace
from datetime import timedelta

from optifisc.domaine.erreurs import AccesRefuse, DonneeInvalide
from optifisc.domaine.journal import EvenementAudit
from optifisc.domaine.utilisateur import Role, Utilisateur

from .autorisation import exiger
from .ports import DepotUtilisateurs, Horloge, Journal, ServiceMotsDePasse

ECHECS_AVANT_BLOCAGE = 5
DUREE_BLOCAGE = timedelta(minutes=15)
MESSAGE_ECHEC = "E-mail ou mot de passe incorrect."


class ServiceComptes:
    def __init__(self, utilisateurs: DepotUtilisateurs, mots_de_passe: ServiceMotsDePasse, journal: Journal,
                 horloge: Horloge):
        self.utilisateurs = utilisateurs
        self.mdp = mots_de_passe
        self.journal = journal
        self.horloge = horloge

    def _tracer(self, qui: str, role: str, action: str, detail: str, dossier_id: str = "") -> None:
        self.journal.ajouter(EvenementAudit(self.horloge.maintenant(), qui, role, action, detail, dossier_id))

    # ------------------------------------------------------------------ UC12 connexion
    def utilisateur_actif(self, email: str) -> Utilisateur | None:
        """Relit le compte à chaque écran : un compte désactivé perd l'accès immédiatement."""
        utilisateur = self.utilisateurs.charger(email)
        return utilisateur if utilisateur and utilisateur.actif else None

    def aucun_compte(self) -> bool:
        return not self.utilisateurs.lister()

    def connecter(self, email: str, mot_de_passe: str) -> Utilisateur:
        email = email.strip().lower()
        maintenant = self.horloge.maintenant()
        utilisateur = self.utilisateurs.charger(email)
        identifiants = self.utilisateurs.identifiants(email)
        if utilisateur is None or identifiants is None or not utilisateur.actif:
            raise AccesRefuse(MESSAGE_ECHEC)                    # même message : ne pas révéler si le compte existe
        echecs, bloque_jusqu = self.utilisateurs.etat_connexion(email)
        if bloque_jusqu and bloque_jusqu > maintenant:
            raise AccesRefuse(f"Compte bloqué après {ECHECS_AVANT_BLOCAGE} essais : réessayer après "
                              f"{bloque_jusqu:%H:%M}.")
        if not self.mdp.verifier(mot_de_passe, *identifiants):
            echecs += 1
            blocage = maintenant + DUREE_BLOCAGE if echecs >= ECHECS_AVANT_BLOCAGE else None
            self.utilisateurs.noter_connexion(email, 0 if blocage else echecs, blocage, None)
            self._tracer(email, utilisateur.role.value, "connexion_refusee",
                         "compte bloqué 15 minutes" if blocage else f"échec {echecs}")
            raise AccesRefuse(MESSAGE_ECHEC)
        self.utilisateurs.noter_connexion(email, 0, None, maintenant)
        self._tracer(email, utilisateur.role.value, "connexion", "")
        return utilisateur

    def changer_mot_de_passe(self, utilisateur: Utilisateur, ancien: str, nouveau: str) -> Utilisateur:
        identifiants = self.utilisateurs.identifiants(utilisateur.email)
        if identifiants is None or not self.mdp.verifier(ancien, *identifiants):
            raise AccesRefuse("Mot de passe actuel incorrect.")
        probleme = self.mdp.probleme(nouveau)
        if probleme:
            raise DonneeInvalide(f"Nouveau mot de passe refusé : {probleme}.")
        self.utilisateurs.changer_mot_de_passe(utilisateur.email, *self.mdp.hacher(nouveau), doit_changer=False)
        self._tracer(utilisateur.email, utilisateur.role.value, "mot_de_passe_change", "")
        return replace(utilisateur, doit_changer_mot_de_passe=False)

    # ------------------------------------------------------------------ UC13 utilisateurs
    def creer_utilisateur(self, admin: Utilisateur | None, email: str, nom: str, role: Role) -> str:
        """Crée un compte et renvoie son mot de passe initial (affiché une seule fois)."""
        exiger(admin, "gerer_utilisateurs")
        email = email.strip().lower()
        if "@" not in email or not nom.strip():
            raise DonneeInvalide("e-mail et nom obligatoires")
        if self.utilisateurs.charger(email):
            raise DonneeInvalide(f"le compte {email} existe déjà")
        mot_de_passe = self.mdp.generer()
        self.utilisateurs.ajouter(Utilisateur(email, nom.strip(), role, True, True), *self.mdp.hacher(mot_de_passe))
        self._tracer(admin.email, admin.role.value, "utilisateur_cree", f"{email} ({role.value})")
        return mot_de_passe

    def creer_premier_administrateur(self, email: str, nom: str) -> str:
        """Initialisation de l'installation : seulement si aucun compte n'existe encore."""
        if self.utilisateurs.lister():
            raise AccesRefuse("des comptes existent déjà : l'initialisation n'est plus possible")
        mot_de_passe = self.mdp.generer()
        self.utilisateurs.ajouter(Utilisateur(email.strip().lower(), nom, Role.ADMIN, True, True),
                                  *self.mdp.hacher(mot_de_passe))
        self._tracer("", "systeme", "installation", f"premier administrateur : {email}")
        return mot_de_passe

    def modifier_utilisateur(self, admin: Utilisateur | None, email: str, role: Role | None = None,
                             actif: bool | None = None) -> Utilisateur:
        exiger(admin, "gerer_utilisateurs")
        cible = self.utilisateurs.charger(email)
        if cible is None:
            raise DonneeInvalide(f"compte inconnu : {email}")
        if cible.email == admin.email and (actif is False or (role and role is not Role.ADMIN)):
            raise DonneeInvalide("un administrateur ne peut pas se désactiver ni se retirer ses propres droits")
        nouveau = replace(cible, role=role or cible.role, actif=cible.actif if actif is None else actif)
        self.utilisateurs.modifier(nouveau)
        self._tracer(admin.email, admin.role.value, "utilisateur_modifie",
                     f"{email} : rôle {nouveau.role.value}, {'actif' if nouveau.actif else 'désactivé'}")
        return nouveau

    def reinitialiser_mot_de_passe(self, admin: Utilisateur | None, email: str) -> str:
        exiger(admin, "gerer_utilisateurs")
        if self.utilisateurs.charger(email) is None:
            raise DonneeInvalide(f"compte inconnu : {email}")
        mot_de_passe = self.mdp.generer()
        self.utilisateurs.changer_mot_de_passe(email, *self.mdp.hacher(mot_de_passe), doit_changer=True)
        self.utilisateurs.noter_connexion(email, 0, None, None)
        self._tracer(admin.email, admin.role.value, "mot_de_passe_reinitialise", email)
        return mot_de_passe

    def lister(self, demandeur: Utilisateur | None) -> list[Utilisateur]:
        exiger(demandeur, "gerer_utilisateurs")
        return self.utilisateurs.lister()
