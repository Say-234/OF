"""E14 — Assistant CGI (UC09). Construit au jalon J11."""
import streamlit as st

from optifisc.interface.streamlit import composants

composants.entete("Assistant CGI", "Retrouver et comprendre un article du CGI 2026 ou du LPF 2024.")
st.info("L'assistant sera disponible au jalon J11.", icon=":material/construction:")
