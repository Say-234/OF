"""Écrans des étapes d'un dossier. Chaque module expose afficher(app, utilisateur, dossier, derniere_balance)."""
import streamlit as st

from optifisc.application.autorisation import peut
from optifisc.interface.streamlit import etat


def bouton_suite(etape: str, libelle: str) -> None:
    """Bouton « étape suivante » en bas d'écran (doc 04, principe 2)."""
    with st.container(horizontal=True, horizontal_alignment="right"):
        st.button(libelle, icon=":material/arrow_forward:", on_click=etat.aller_a_l_etape, args=(etape,),
                  key=f"suite_{etape}")


def peut_modifier(utilisateur, dossier) -> bool:
    """Saisies actives seulement si l'utilisateur prépare ce dossier et qu'il n'est pas figé."""
    return peut(utilisateur, "preparer_dossier", dossier) and not dossier.est_fige


def bandeau_fige(dossier) -> None:
    if dossier.est_fige:
        st.info("Dossier en lecture seule : il est soumis, validé ou livré.", icon=":material/lock:")
