"""E17 — Utilisateurs (UC13, administrateur) : créer, changer de rôle, désactiver, réinitialiser, attribuer."""
import streamlit as st

from optifisc.domaine.utilisateur import LIBELLES_ROLE, Role
from optifisc.interface.streamlit import composants, etat

app = etat.application()
utilisateur = etat.utilisateur()

composants.entete("Utilisateurs", "Comptes du cabinet. Un compte est désactivé, jamais supprimé, pour garder un "
                                  "journal lisible.")
comptes = composants.executer(lambda: app.comptes.lister(utilisateur))
if comptes is None:
    st.stop()

evenement = st.dataframe([{"Nom": c.nom, "E-mail": c.email, "Rôle": c.libelle_role,
                           "État": "actif" if c.actif else "désactivé"} for c in comptes],
                         hide_index=True, on_select="rerun", selection_mode="single-row", key="tableau_comptes",
                         alt="Comptes du cabinet")

if evenement.selection.rows:
    cible = comptes[evenement.selection.rows[0]]
    with composants.carte():
        st.markdown(f"**{cible.nom}** · {cible.email}")
        with st.container(horizontal=True, vertical_alignment="bottom"):
            role = st.selectbox("Rôle", list(Role), index=list(Role).index(cible.role),
                                format_func=LIBELLES_ROLE.get, key=f"role_{cible.email}")
            if st.button("Enregistrer le rôle", key=f"r_{cible.email}"):
                if composants.executer(lambda: app.comptes.modifier_utilisateur(utilisateur, cible.email, role=role),
                                       "Rôle modifié"):
                    st.rerun()
            libelle = "Désactiver" if cible.actif else "Réactiver"
            if st.button(libelle, key=f"a_{cible.email}"):
                basculer = lambda: app.comptes.modifier_utilisateur(utilisateur, cible.email,  # noqa: E731
                                                                    actif=not cible.actif)
                if composants.executer(basculer, "Compte modifié"):
                    st.rerun()
            if st.button("Réinitialiser le mot de passe", key=f"m_{cible.email}"):
                mot_de_passe = composants.executer(lambda: app.comptes.reinitialiser_mot_de_passe(utilisateur,
                                                                                                  cible.email))
                if mot_de_passe:
                    st.success(f"Nouveau mot de passe provisoire (affiché une seule fois) : **{mot_de_passe}**",
                               icon=":material/key:")

with st.expander("Créer un compte", icon=":material/person_add:"):
    with st.form("nouveau_compte"):
        nom = st.text_input("Nom")
        email = st.text_input("E-mail", type="email")
        role = st.selectbox("Rôle", list(Role), format_func=LIBELLES_ROLE.get)
        if st.form_submit_button("Créer le compte", type="primary"):
            mot_de_passe = composants.executer(lambda: app.comptes.creer_utilisateur(utilisateur, email, nom, role))
            if mot_de_passe:
                st.success(f"Compte créé. Mot de passe initial, à changer à la première connexion (affiché une "
                           f"seule fois) : **{mot_de_passe}**", icon=":material/key:")

st.subheader("Attribuer un dossier", anchor=False)
dossiers = [r.dossier for r in app.dossiers.lister(utilisateur)]
collaborateurs = [c for c in comptes if c.actif and c.role is not Role.ADMIN]
if dossiers and collaborateurs:
    with st.container(horizontal=True, vertical_alignment="bottom"):
        dossier = st.selectbox("Dossier", dossiers, format_func=lambda d: f"{d.raison_sociale} ({d.responsable})")
        responsable = st.selectbox("Responsable", collaborateurs, format_func=lambda c: f"{c.nom} — {c.email}")
        if st.button("Attribuer"):
            if composants.executer(lambda: app.dossiers.attribuer(utilisateur, dossier.id, responsable.email),
                                   "Dossier attribué"):
                st.rerun()
else:
    st.caption("Aucun dossier à attribuer.")
composants.pied_de_page()
