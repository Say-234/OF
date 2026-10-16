"""Point d'entrée Streamlit : garde d'authentification et navigation selon le rôle (doc 04).

Lancer depuis le dossier OF/ :  streamlit run src/optifisc/interface/streamlit/app.py
Aucune logique métier ici : chaque écran appelle les cas d'usage de la couche Application.
"""
import streamlit as st

from optifisc.domaine.utilisateur import Role
from optifisc.interface.streamlit import etat

st.set_page_config(page_title="OptiFisc", page_icon=":material/account_balance:", layout="wide")

app = etat.application()
utilisateur = etat.utilisateur()

if utilisateur is None:
    page = st.navigation([st.Page("app_pages/connexion.py", title="Connexion", icon=":material/login:")],
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
    reglages = [st.Page("app_pages/profil.py", title="Mon profil", icon=":material/person:")]
    if utilisateur.role is Role.ADMIN:
        reglages.append(st.Page("app_pages/utilisateurs.py", title="Utilisateurs", icon=":material/group:"))
    page = st.navigation({"Pilotage": pilotage, "Outils": outils, "Réglages": reglages})

if utilisateur is not None:
    with st.sidebar:
        if app.mode == "demo":
            st.badge("Démonstration · données fictives", color="orange", icon=":material/science:",
                     help="N'importez aucune donnée réelle sur cette instance.")
        st.markdown(f"**{utilisateur.nom}**  \n:gray[{utilisateur.libelle_role}]")
        if st.button("Se déconnecter", icon=":material/logout:", type="tertiary"):
            app.dependances.tracer(utilisateur, "deconnexion")
            etat.deconnecter()
            st.rerun()

page.run()
