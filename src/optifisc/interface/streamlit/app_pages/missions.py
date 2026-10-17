"""E15 — Mes missions : le journal de missions complet du rôle connecté (tutoriel rejouable)."""
import streamlit as st

from optifisc.interface.streamlit import composants, etat, missions

app = etat.application()
utilisateur = etat.utilisateur()
tuto = app.tutoriel.tutoriel(utilisateur, etat.dossier_id())
en_cours = tuto.en_cours

actions = composants.entete("Mes missions", f"Votre parcours de {utilisateur.libelle_role.lower()}, pas à pas. "
                                            "Les étapes se cochent toutes seules au fil de votre travail.")
with actions:
    if st.button("Recommencer le tutoriel", icon=":material/restart_alt:", type="tertiary",
                 help="Efface vos coches manuelles et remontre l'accueil du tutoriel. Vos données ne changent pas."):
        app.tutoriel.recommencer(utilisateur)
        st.toast("Tutoriel recommencé.", icon=":material/restart_alt:")
        st.rerun()

with composants.carte():
    gauche, droite = st.columns([2, 1], vertical_alignment="center")
    with gauche:
        st.progress(tuto.faites / tuto.total, text=f"**{tuto.faites}** étape(s) accomplie(s) sur {tuto.total}")
        if tuto.dossier is not None:
            st.caption(f"Étapes du dossier lues sur : **{tuto.dossier.raison_sociale}** "
                       "(le dossier ouvert, sinon le plus avancé).")
    with droite, st.container(horizontal=True, horizontal_alignment="right"):
        if en_cours and st.button("Continuer : " + en_cours[1].titre, type="primary", icon=":material/near_me:"):
            missions.aller(tuto, en_cours[1])
        elif en_cours is None:
            composants.badge("Toutes les missions sont accomplies", "fait")

for numero, mission in enumerate(tuto.missions, 1):
    with composants.carte():
        with st.container(horizontal=True, vertical_alignment="center"):
            st.markdown(f"#### Mission {numero} · {mission.titre}")
            missions.badge_mission(mission, en_cours is not None and en_cours[0].id == mission.id)
        st.caption(f"{mission.objectif} · {mission.faites}/{len(mission.etapes)}")
        for etape in mission.etapes:
            courante = en_cours is not None and en_cours[1].id == etape.id
            icone = ":green[:material/check_circle:]" if etape.faite else (
                ":primary[:material/radio_button_checked:]" if courante else ":gray[:material/radio_button_unchecked:]")
            with st.container(horizontal=True, vertical_alignment="center"):
                with st.container():
                    st.markdown(f"{icone} **{etape.titre}**")
                    st.caption(etape.consigne + ("" if etape.automatique else " · à cocher vous-même"))
                if not etape.automatique:
                    coche = st.checkbox("Fait", value=etape.faite, key=f"coche_{etape.id}")
                    if coche != etape.faite:
                        app.tutoriel.cocher(utilisateur, etape.id, coche)
                        st.rerun()
                if not etape.faite and st.button("Y aller", key=f"aller_{etape.id}", icon=":material/arrow_forward:",
                                                 type="primary" if courante else "secondary"):
                    missions.aller(tuto, etape)

composants.pied_de_page()
