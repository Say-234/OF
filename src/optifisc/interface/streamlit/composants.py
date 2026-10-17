"""Composants d'interface réutilisables (doc 05, A.6). Natifs Streamlit d'abord, aucun HTML sur mesure.

Règle : la couleur porte un statut et n'est jamais seule (icône + texte) ; le vert d'accent est réservé aux actions.
"""
from collections.abc import Callable
from decimal import Decimal
from pathlib import Path

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


DOSSIER = Path(__file__).parent
STATIQUE = DOSSIER / "static"
_cartes = {"numero": 0}


def preparer_page() -> None:
    """À appeler en tête de chaque exécution (app.py) : style des cartes, logo s'il existe, compteur de cartes."""
    _cartes["numero"] = 0
    st.html(f"<style>{(DOSSIER / 'style.css').read_text(encoding='utf-8')}</style>")
    for nom in ("logo.svg", "logo.png"):                     # logo professionnel déposé dans static/ (doc 05)
        if (STATIQUE / nom).exists():
            icone = next((STATIQUE / i for i in ("icone.svg", "icone.png") if (STATIQUE / i).exists()), None)
            st.logo(str(STATIQUE / nom), size="large", icon_image=str(icone) if icone else None)
            break


def carte(**options):
    """Carte blanche arrondie (fond teinté autour) : remplace st.container(border=True) dans toute l'interface.

    La clé « carte-N » donne à Streamlit la classe CSS st-key-carte-N, que style.css habille.
    """
    _cartes["numero"] += 1
    return st.container(border=True, key=f"carte-{_cartes['numero']}", **options)


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


def entete_dossier(dossier: Dossier, libelle_secteur: str, date_arrete, responsable: str) -> None:
    """Ligne d'identité du dossier, au-dessus des onglets d'étapes."""
    st.subheader(dossier.raison_sociale, anchor=False)
    with st.container(horizontal=True, vertical_alignment="center"):
        badge_etat(dossier.etat)
        if dossier.demonstration:
            st.badge("Démonstration", color="gray", icon=":material/science:")
        st.caption(f"IS {dossier.exercice} · {libelle_secteur} · balance au {formats.jour(date_arrete)} · "
                   f"responsable : {responsable}")


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


TONS = {"fait": ("green", "check_circle"), "a_faire": ("orange", "error"), "risque": ("red", "cancel"),
        "info": ("gray", "info")}


def liste_de_points(points: list[tuple[str, str]], titre: str = "") -> None:
    """Liste compacte de points dans un seul cadre : une ligne par point, icône colorée + texte (doc 05, A.2).

    points : [(ton, texte)] avec ton ∈ fait | a_faire | risque | info. Évite d'empiler des encadrés colorés.
    """
    with carte():
        if titre:
            st.markdown(f"**{titre}**")
        for ton, texte in points:
            couleur, icone = TONS[ton]
            st.markdown(f":{couleur}[:material/{icone}:] {texte}")


ACTIONS = {"dossier_cree": "Dossier créé", "balance_importee": "Balance importée",
           "hypotheses_definies": "Hypothèses enregistrées", "saisie": "Saisie d'un retraitement",
           "calcul_effectue": "Calcul effectué", "decision_acomptes": "Décision sur les acomptes",
           "scenario_enregistre": "Scénario enregistré", "scenario_supprime": "Scénario supprimé",
           "decision_leviers": "Décision sur les leviers", "dossier_soumis": "Dossier soumis",
           "dossier_valide": "Dossier validé", "dossier_renvoye": "Dossier renvoyé",
           "dossier_rouvert": "Dossier rouvert", "livrables_provisoires": "Livrables provisoires générés",
           "livrables_definitifs": "Livrables définitifs générés", "appel_ia": "Appel à l'IA",
           "ia_bloquee_pare_feu": "IA bloquée par le pare-feu", "proposition_acceptee": "Proposition acceptée",
           "proposition_ecartee": "Proposition écartée", "regle_validee": "Règle validée",
           "regle_remise_a_valider": "Règle remise à valider", "dossier_attribue": "Dossier attribué",
           "connexion": "Connexion", "connexion_refusee": "Connexion refusée", "deconnexion": "Déconnexion",
           "mot_de_passe_change": "Mot de passe changé", "utilisateur_cree": "Utilisateur créé",
           "utilisateur_modifie": "Utilisateur modifié", "mot_de_passe_reinitialise": "Mot de passe réinitialisé",
           "installation": "Installation"}


def action(code: str) -> str:
    """Libellé lisible d'une action du journal (les codes sont sans accents, l'affichage non)."""
    return ACTIONS.get(code, code.replace("_", " ").capitalize())


def nom(app, email: str) -> str:
    """Nom affiché d'un utilisateur (plutôt que son e-mail, que l'affichage transformerait en lien)."""
    if not email:
        return "système"
    compte = app.comptes.utilisateurs.charger(email)
    return compte.nom if compte else email.split("@")[0]


def vide(texte: str) -> None:
    st.info(texte, icon=":material/info:")


def pied_de_page() -> None:
    st.divider()
    st.caption("OptiFisc · CGI Bénin 2026 · Les montants sont calculés par le moteur de règles ; "
               "l'IA ne calcule jamais l'impôt. Aide à la décision, à valider par l'expert-comptable.")
