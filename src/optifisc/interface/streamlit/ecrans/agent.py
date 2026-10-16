"""Panneau « Propositions de l'agent » de l'écran Leviers (UC14). Construit au jalon J11."""
import streamlit as st


def afficher(app, utilisateur, dossier, modifiable):
    with st.container(border=True):
        st.markdown("**Propositions de l'agent**")
        st.caption("L'agent IA proposera ici des pistes d'optimisation (jalon J11). "
                   "Les montants resteront calculés par le moteur.")
