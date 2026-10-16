"""E16 — Journal d'audit (UC11) : qui a fait quoi, quand, sur quel dossier. Lecture seule."""
import streamlit as st

from optifisc.interface.streamlit import composants, etat, formats

app = etat.application()
utilisateur = etat.utilisateur()

composants.entete("Journal d'audit", "Chronologie des actions, en ajout seul : aucune entrée ne peut être modifiée.")
portee = "Dossier ouvert" if etat.dossier_id() else "Tous mes dossiers"
if etat.dossier_id():
    portee = st.segmented_control("Portée", ["Dossier ouvert", "Tous"], default="Dossier ouvert", required=True,
                                  label_visibility="collapsed")
evenements = composants.executer(lambda: app.dossiers.journal(
    utilisateur, etat.dossier_id() if portee == "Dossier ouvert" else None)) or []
actions = sorted({e.action for e in evenements}, key=composants.action)
filtre = st.multiselect("Types d'action", actions, format_func=composants.action, placeholder="Toutes les actions")
lignes = [{"Date": formats.horodatage(e.quand), "Utilisateur": e.utilisateur or "système", "Rôle": e.role,
           "Dossier": e.dossier_id, "Action": composants.action(e.action), "Détail": e.detail,
           "Référentiel": e.version_referentiel} for e in evenements if not filtre or e.action in filtre]
if lignes:
    st.dataframe(lignes, hide_index=True, alt="Journal d'audit")
else:
    composants.vide("Aucun événement.")
composants.pied_de_page()
