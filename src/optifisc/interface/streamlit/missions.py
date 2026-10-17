"""Affichage du journal de missions (tutoriel par rôle) : résumé dans la barre latérale, accueil à la première
connexion, bandeau « mission en cours » dans l'onglet concerné du dossier. La logique est dans
application/tutoriel.py ; ici, seulement l'affichage et la navigation.
"""
import streamlit as st

from . import composants, etat

PAGES = {"dossiers": "app_pages/dossiers.py", "dossier": "app_pages/dossier.py",
         "utilisateurs": "app_pages/utilisateurs.py", "journal": "app_pages/journal.py",
         "referentiel": "app_pages/referentiel.py", "missions": "app_pages/missions.py"}


def aller(tuto, etape) -> None:
    """Emmène l'utilisateur là où l'étape se fait (le bon dossier, le bon onglet)."""
    if etape.page == "dossier":
        if tuto.dossier is None:
            st.switch_page(PAGES["dossiers"])
        etat.ouvrir_dossier(tuto.dossier.id, etape.etape_dossier or "synthese")
    st.switch_page(PAGES[etape.page])


def resume_barre_laterale(app, utilisateur) -> None:
    tuto = app.tutoriel.tutoriel(utilisateur, etat.dossier_id())
    with st.container(border=True, key="mission-barre"):
        st.markdown("**:primary[:material/flag:] Journal de missions**")
        st.progress(tuto.faites / tuto.total, text=f"{tuto.faites} étape(s) sur {tuto.total}")
        en_cours = tuto.en_cours
        if en_cours is None:
            st.caption("Toutes vos missions sont accomplies.")
            return
        mission, etape = en_cours
        st.caption(f"{mission.titre} · **{etape.titre}**")
        if st.button("M'y emmener", icon=":material/near_me:", key="mission_aller", width="stretch"):
            aller(tuto, etape)


@st.dialog("Votre journal de missions", width="large")
def _accueil_tutoriel(app, utilisateur) -> None:
    tuto = app.tutoriel.tutoriel(utilisateur, etat.dossier_id())
    st.markdown(f"Bienvenue, **{utilisateur.nom}**. En tant que **{utilisateur.libelle_role.lower()}**, "
                "voici vos missions. Elles se cochent toutes seules au fil de votre travail.")
    for numero, mission in enumerate(tuto.missions, 1):
        st.markdown(f"**Mission {numero} · {mission.titre}** · :gray[{mission.objectif}]")
    st.caption("Vous retrouverez ce journal dans la barre latérale et dans « Mes missions ».")
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Plus tard", key="tuto_plus_tard"):
            st.rerun()
        en_cours = tuto.en_cours
        if en_cours and st.button("Commencer", type="primary", icon=":material/play_arrow:", key="tuto_commencer"):
            aller(tuto, en_cours[1])


def accueil_premiere_connexion(app, utilisateur) -> None:
    """Montre l'accueil du tutoriel une seule fois (il reste accessible ensuite depuis « Mes missions »)."""
    if not app.tutoriel.tutoriel(utilisateur).vu:
        app.tutoriel.marquer_vu(utilisateur)
        _accueil_tutoriel(app, utilisateur)


def bandeau_dans_le_dossier(app, utilisateur, dossier, onglet: str) -> None:
    """Si la prochaine étape du tutoriel se fait dans cet onglet de CE dossier : bandeau de consigne."""
    tuto = app.tutoriel.tutoriel(utilisateur, dossier.id)
    en_cours = tuto.en_cours
    if en_cours is None or tuto.dossier is None or tuto.dossier.id != dossier.id:
        return
    mission, etape = en_cours
    if etape.page != "dossier" or etape.etape_dossier != onglet:
        return
    with st.container(border=True, key=f"mission-{etape.id}", horizontal=True, vertical_alignment="center"):
        with st.container():
            st.markdown(f":primary[:material/flag:] **Mission · {mission.titre}** — {etape.titre}")
            st.caption(etape.consigne)
        if not etape.automatique and st.button("Marquer comme fait", icon=":material/check:",
                                               key=f"fait_{etape.id}"):
            app.tutoriel.cocher(utilisateur, etape.id)
            st.rerun()


def badge_mission(mission, est_en_cours: bool) -> None:
    if mission.terminee:
        composants.badge("Terminée", "fait")
    elif est_en_cours:
        st.badge("En cours", color="green", icon=":material/play_circle:")
    else:
        st.badge("À venir", color="gray", icon=":material/schedule:")
