"""E01 — Connexion (UC12). E-mail + mot de passe ; blocage après 5 échecs (géré par le cas d'usage)."""
import streamlit as st

from optifisc.domaine.utilisateur import Role
from optifisc.interface.streamlit import composants, etat

app = etat.application()

centre = st.container(horizontal=True, horizontal_alignment="center")
with centre.container(width=440):
    st.space("medium")
    st.page_link("app_pages/accueil.py", label="Découvrir OptiFisc", icon=":material/arrow_back:")
    st.header("OptiFisc", anchor=False)
    st.caption("Pilotage de l'impôt sur les sociétés en cours d'exercice · CGI Bénin 2026")
    if app.mode == "demo":
        st.warning("Instance de démonstration : dossiers fictifs uniquement. N'importez aucune donnée réelle.",
                   icon=":material/science:")
    if st.session_state.pop("session_expiree", False):
        st.info("Session expirée après 30 minutes d'inactivité : reconnectez-vous.", icon=":material/schedule:")

    if app.comptes.aucun_compte():
        st.subheader("Installation", anchor=False)
        st.caption("Aucun compte n'existe encore : créez le premier administrateur.")
        with st.form("installation"):
            nom = st.text_input("Nom")
            email = st.text_input("E-mail", type="email")
            if st.form_submit_button("Créer l'administrateur", type="primary"):
                mot_de_passe = composants.executer(lambda: app.comptes.creer_premier_administrateur(email, nom))
                if mot_de_passe:
                    st.success(f"Compte créé. Mot de passe initial, affiché une seule fois : **{mot_de_passe}**",
                               icon=":material/key:")
        st.stop()

    if app.mode == "demo" and app.mot_de_passe_demo:
        st.markdown("**Entrer directement**")
        with st.container(horizontal=True):
            for role, libelle in ((Role.COLLABORATEUR, "Collaborateur"), (Role.EXPERT, "Expert-comptable"),
                                  (Role.ADMIN, "Administrateur")):
                if st.button(libelle, key=f"demo_{role.value}", icon=":material/login:"):
                    compte = composants.executer(lambda role=role: app.entrer_en_demo(role))
                    if compte:
                        etat.connecter(compte)
                        st.rerun()
        st.caption("Ou connectez-vous avec un compte, comme en cabinet :")

    with st.form("connexion"):
        email = st.text_input("E-mail", type="email", autocomplete="username", placeholder="prenom.nom@cabinet.bj")
        mot_de_passe = st.text_input("Mot de passe", type="password", autocomplete="current-password")
        envoye = st.form_submit_button("Se connecter", type="primary", width="stretch")
    if envoye:
        compte = composants.executer(lambda: app.comptes.connecter(email, mot_de_passe))
        if compte:
            etat.connecter(compte)
            st.rerun()

    if app.mode == "demo" and app.aide_demo:
        with st.expander("Comptes de démonstration", icon=":material/science:"):
            st.markdown(app.aide_demo)
