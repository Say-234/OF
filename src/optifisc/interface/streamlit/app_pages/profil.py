"""E18 — Mon profil, et E02 — changement obligatoire du mot de passe à la première connexion."""
import streamlit as st

from optifisc.interface.streamlit import composants, etat

app = etat.application()
utilisateur = etat.utilisateur()

composants.entete("Mon profil", f"{utilisateur.nom} · {utilisateur.email} · {utilisateur.libelle_role}")
if utilisateur.doit_changer_mot_de_passe:
    st.warning("Première connexion : choisissez votre mot de passe personnel pour continuer.", icon=":material/key:")

with st.form("mot_de_passe", width=440):
    st.markdown("**Changer le mot de passe**")
    ancien = st.text_input("Mot de passe actuel", type="password", autocomplete="current-password")
    nouveau = st.text_input("Nouveau mot de passe", type="password", autocomplete="new-password",
                            help="8 caractères au moins ; les mots de passe trop courants sont refusés.")
    confirmation = st.text_input("Confirmer le nouveau mot de passe", type="password", autocomplete="new-password")
    if st.form_submit_button("Changer le mot de passe", type="primary"):
        if nouveau != confirmation:
            st.error("Les deux saisies du nouveau mot de passe sont différentes.", icon=":material/error:")
        elif composants.executer(lambda: app.comptes.changer_mot_de_passe(utilisateur, ancien, nouveau),
                                 "Mot de passe changé"):
            st.rerun()
