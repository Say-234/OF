"""Accès à st.session_state : SEULEMENT des identifiants et des préférences d'affichage (doc 05, C.1, règle 5).

Jamais de résultat de calcul en session : il est recalculé à chaque affichage depuis la base,
ce qui évite d'afficher un résultat périmé.
"""
import os
from datetime import datetime, timedelta

import streamlit as st

from optifisc.composition import Application, construire
from optifisc.domaine.utilisateur import Utilisateur

DUREE_SESSION = timedelta(minutes=30)       # déconnexion après 30 minutes d'inactivité (doc 02, §5.3)


def _secrets_vers_environnement() -> None:
    """Hébergement en ligne : les réglages (clé d'API, mode, mot de passe de démo) sont dans les « secrets »
    de la plateforme. On les recopie en variables d'environnement, lues par composition.py comme le fichier .env."""
    try:
        for cle, valeur in st.secrets.items():
            if isinstance(valeur, str):
                os.environ.setdefault(cle, valeur)
    except Exception:  # pas de fichier de secrets en local : c'est le cas normal
        pass


@st.cache_resource
def application() -> Application:
    """Une seule instance pour tout le serveur : référentiel chargé et validé une fois."""
    _secrets_vers_environnement()
    return construire()


def utilisateur() -> Utilisateur | None:
    email = st.session_state.get("email")
    if not email:
        return None
    derniere = st.session_state.get("derniere_activite")
    if derniere and datetime.now() - derniere > DUREE_SESSION:
        deconnecter()
        st.session_state["session_expiree"] = True
        return None
    st.session_state["derniere_activite"] = datetime.now()
    compte = application().comptes.utilisateur_actif(email)
    if compte is None:
        deconnecter()
    return compte


def connecter(compte: Utilisateur) -> None:
    st.session_state["email"] = compte.email
    st.session_state["derniere_activite"] = datetime.now()
    st.session_state.pop("session_expiree", None)


def deconnecter() -> None:
    for cle in ("email", "derniere_activite", "dossier_id", "etape"):
        st.session_state.pop(cle, None)


def dossier_id() -> str | None:
    return st.session_state.get("dossier_id")


def ouvrir_dossier(identifiant: str, etape: str = "synthese") -> None:
    st.session_state["dossier_id"] = identifiant
    st.session_state["etape"] = etape


def etape() -> str:
    return st.session_state.get("etape", "synthese")


def aller_a_l_etape(identifiant: str) -> None:
    st.session_state["etape"] = identifiant
