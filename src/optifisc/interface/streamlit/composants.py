"""Composants d'interface réutilisables (doc 05, A.6). Natifs Streamlit d'abord, aucun HTML sur mesure.

Règle : la couleur porte un statut et n'est jamais seule (icône + texte) ; le bleu est réservé aux actions.
"""
from collections.abc import Callable
from decimal import Decimal

import streamlit as st

from optifisc.domaine.dossier import Dossier, EtatDossier
from optifisc.domaine.erreurs import ErreurMetier

from . import formats

# État du dossier → (libellé, couleur, icône)
ETATS = {
    EtatDossier.BROUILLON: ("Brouillon", "gray", ":material/draft:"),
    EtatDossier.EN_PREPARATION: ("En préparation", "orange", ":material/edit_note:"),
    EtatDossier.CALCULE: ("Calculé", "gray", ":material/calculate:"),
    EtatDossier.A_VALIDER: ("À valider", "orange", ":material/pending_actions:"),
    EtatDossier.VALIDE: ("Validé", "green", ":material/verified:"),
    EtatDossier.LIVRE: ("Livré", "green", ":material/task_alt:"),
}


def entete(titre: str, sous_titre: str = ""):
    """Gabarit commun : un titre et UNE ligne qui dit à quoi sert l'écran.

    Renvoie une zone à droite du titre, où placer l'action principale de l'écran (doc 05, A.5).
    """
    gauche, droite = st.columns([3, 1], vertical_alignment="bottom")
    with gauche:
        st.header(titre, anchor=False)
        if sous_titre:
            st.caption(sous_titre)
    return droite.container(horizontal=True, horizontal_alignment="right")


def badge_etat(etat: EtatDossier) -> None:
    libelle, couleur, icone = ETATS[etat]
    st.badge(libelle, color=couleur, icon=icone)


def badge(texte: str, ton: str) -> None:
    """ton : fait | a_faire | risque | info."""
    couleur, icone = {"fait": ("green", ":material/check_circle:"), "a_faire": ("orange", ":material/error:"),
                      "risque": ("red", ":material/cancel:"), "info": ("gray", ":material/info:")}[ton]
    st.badge(texte, color=couleur, icon=icone)


def entete_dossier(dossier: Dossier, libelle_secteur: str, date_arrete) -> None:
    """Ligne d'identité du dossier, sous le titre de chaque étape."""
    with st.container(horizontal=True, vertical_alignment="center"):
        st.markdown(f"**{dossier.raison_sociale}** · IS {dossier.exercice} · {libelle_secteur} · "
                    f"balance au {formats.jour(date_arrete)}" + ("  ·  :gray[dossier de démonstration]"
                                                                 if dossier.demonstration else ""))
        badge_etat(dossier.etat)
        st.caption(f"Resp. {dossier.responsable or '—'}")


def executer(action: Callable, succes: str = ""):
    """Lance un cas d'usage ; une erreur métier devient un message clair, jamais une trace Python."""
    try:
        resultat = action()
    except ErreurMetier as exc:
        st.error(str(exc), icon=":material/error:")
        return None
    if succes:
        st.toast(succes, icon=":material/check_circle:")
    return resultat


def champ_montant(libelle: str, cle: str, valeur: Decimal | None = None, aide: str | None = None,
                  desactive: bool = False) -> tuple[Decimal | None, bool]:
    """Saisie d'un montant en FCFA (texte aligné, séparateur de milliers). Renvoie (montant, valide)."""
    texte = st.text_input(f"{libelle} (FCFA)", value="" if valeur is None else formats.montant(valeur), key=cle,
                          help=aide, disabled=desactive, placeholder="ex. 1 500 000")
    try:
        return formats.lire_montant(texte), True
    except ValueError as exc:
        st.caption(f":red[:material/error: {exc}]")
        return None, False


def colonne_montant(titre: str):
    """Colonne de montants déjà formatés, alignés à droite (chiffres en espace fine)."""
    return st.column_config.TextColumn(titre, alignment="right")


def vide(texte: str) -> None:
    st.info(texte, icon=":material/info:")


def pied_de_page() -> None:
    st.divider()
    st.caption("OptiFisc · CGI Bénin 2026 · Les montants sont calculés par le moteur de règles ; "
               "l'IA ne calcule jamais l'impôt. Aide à la décision, à valider par l'expert-comptable.")
