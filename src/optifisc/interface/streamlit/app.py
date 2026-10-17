"""Point d'entrée Streamlit : garde d'authentification et navigation selon le rôle (doc 04).

Lancer depuis le dossier OF/ :  streamlit run src/optifisc/interface/streamlit/app.py
Aucune logique métier ici : chaque écran appelle les cas d'usage de la couche Application.
"""
import streamlit as st

from optifisc.domaine.utilisateur import Role
from optifisc.interface.streamlit import composants, etat, missions

st.set_page_config(page_title="OptiFisc", page_icon=":material/account_balance:", layout="wide")

app = etat.application()
utilisateur = etat.utilisateur()
composants.preparer_page()

if utilisateur is None:
    # accueil d'abord (présentation de l'application), puis connexion (doc 04, E00 et E01)
    page = st.navigation([st.Page("app_pages/accueil.py", title="Accueil", icon=":material/home:", default=True),
                          st.Page("app_pages/connexion.py", title="Connexion", icon=":material/login:")],
                         position="hidden")
elif utilisateur.doit_changer_mot_de_passe:
    page = st.navigation([st.Page("app_pages/profil.py", title="Mon profil", icon=":material/person:")],
                         position="hidden")
else:
    pilotage = [st.Page("app_pages/dossiers.py", title="Dossiers", icon=":material/folder_open:", default=True),
                st.Page("app_pages/dossier.py", title="Dossier ouvert", icon=":material/description:")]
    outils = [st.Page("app_pages/assistant.py", title="Assistant CGI", icon=":material/menu_book:"),
              st.Page("app_pages/referentiel.py", title="Référentiel des règles", icon=":material/rule:"),
              st.Page("app_pages/journal.py", title="Journal d'audit", icon=":material/history:")]
    guide = [st.Page("app_pages/missions.py", title="Mes missions", icon=":material/flag:"),
             st.Page("app_pages/accueil.py", title="Découvrir OptiFisc", icon=":material/explore:")]
    reglages = [st.Page("app_pages/profil.py", title="Mon profil", icon=":material/person:")]
    if utilisateur.role is Role.ADMIN:
        reglages.append(st.Page("app_pages/utilisateurs.py", title="Utilisateurs", icon=":material/group:"))
    page = st.navigation({"Pilotage": pilotage, "Guide": guide, "Outils": outils, "Réglages": reglages})

if utilisateur is not None:
    with st.sidebar:
        if app.mode == "demo":
            st.badge("Démonstration · données fictives", color="orange", icon=":material/science:",
                     help="N'importez aucune donnée réelle sur cette instance.")
            roles = {Role.COLLABORATEUR: "Collaborateur", Role.EXPERT: "Expert", Role.ADMIN: "Admin"}
            choix = st.segmented_control("Jouer le rôle de", list(roles), format_func=roles.get,
                                         default=utilisateur.role, key=f"role_demo_{utilisateur.role.value}")
            if choix and choix is not utilisateur.role:
                compte = app.entrer_en_demo(choix)
                dossier_ouvert = etat.dossier_id()
                etat.connecter(compte)
                if dossier_ouvert:
                    etat.ouvrir_dossier(dossier_ouvert, etat.etape())
                st.rerun()
        if not utilisateur.doit_changer_mot_de_passe:
            missions.resume_barre_laterale(app, utilisateur)
        st.markdown(f"**{utilisateur.nom}**  \n:gray[{utilisateur.libelle_role}]")
        if st.button("Se déconnecter", icon=":material/logout:", type="tertiary"):
            app.dependances.tracer(utilisateur, "deconnexion")
            etat.deconnecter()
            st.rerun()

if utilisateur is not None and not utilisateur.doit_changer_mot_de_passe:
    missions.accueil_premiere_connexion(app, utilisateur)     # une seule fois ; rejouable depuis « Mes missions »
page.run()
