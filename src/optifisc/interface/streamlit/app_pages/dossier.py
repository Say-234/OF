"""E05 à E13 — un dossier ouvert : en-tête d'identité, onglets d'étapes, puis l'écran de l'étape choisie.

Un seul repère de navigation dans le dossier (doc 05, A.1) : les onglets d'étapes, avec leur statut.
"""
import streamlit as st

from optifisc.interface.streamlit import composants, etat, missions
from optifisc.interface.streamlit.ecrans import (
    acomptes,
    balance,
    calcul,
    hypotheses,
    leviers,
    livrer,
    retraitements,
    synthese,
)

ECRANS = {"synthese": synthese, "balance": balance, "hypotheses": hypotheses, "retraitements": retraitements,
          "calcul": calcul, "leviers": leviers, "acomptes": acomptes, "livrer": livrer}

app = etat.application()
utilisateur = etat.utilisateur()
dossier_id = etat.dossier_id()

if not dossier_id:
    composants.entete("Dossier ouvert", "Aucun dossier n'est ouvert.")
    composants.vide("Choisissez un dossier dans la liste des dossiers.")
    st.page_link("app_pages/dossiers.py", label="Aller à la liste des dossiers", icon=":material/folder_open:")
    st.stop()

dossier = composants.executer(lambda: app.dossiers.ouvrir(utilisateur, dossier_id))
if dossier is None:
    st.stop()

derniere_balance = app.dependances.balances.derniere(dossier.id)
etapes = app.dossiers.etapes(dossier)
libelles = {"synthese": "Synthèse"}
for e in etapes:
    libelles[e.id] = f"{':material/check: ' if e.faite else ''}{e.numero} {e.libelle}"

composants.entete_dossier(dossier, app.referentiel.parametres.libelles_secteur[dossier.secteur.value].split(" (")[0],
                          derniere_balance[2] if derniere_balance else None,
                          composants.nom(app, dossier.responsable))
if "etape" not in st.session_state or st.session_state["etape"] not in ECRANS:
    st.session_state["etape"] = "synthese"
choix = st.segmented_control("Étape du dossier", list(ECRANS), format_func=libelles.get, key="etape",
                             required=True, label_visibility="collapsed")

missions.bandeau_dans_le_dossier(app, utilisateur, dossier, choix)
etape = next((e for e in etapes if e.id == choix), None)
if etape is not None and not etape.accessible:
    composants.vide(f"Étape pas encore accessible : {etape.raison}")
else:
    ECRANS[choix].afficher(app, utilisateur, dossier, derniere_balance)

composants.pied_de_page()
