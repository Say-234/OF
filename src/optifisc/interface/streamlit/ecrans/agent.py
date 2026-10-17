"""Panneau « Propositions de l'agent » de l'écran Leviers (UC14), séparé visuellement du moteur (doc 05, D5.8).

Le seul montant affiché sous une proposition est le gain calculé par le MOTEUR. La confiance vient du
juge déterministe (doc 01, A.4) : sous le seuil, le badge « confiance faible » invite à vérifier en priorité.
"""
import streamlit as st

from optifisc.application.agent.juge import SEUIL_CONFIANCE
from optifisc.interface.streamlit import composants, formats


@st.dialog("Écarter la proposition")
def _ecarter(app, utilisateur, dossier, proposition):
    st.write(proposition.titre)
    motif = st.text_area("Motif (obligatoire)", placeholder="ex. pas de cession d'immobilisation prévue")
    if st.button("Écarter", type="primary"):
        if composants.executer(lambda: app.agent.decider(utilisateur, dossier.id, proposition.id, False, motif),
                               "Proposition écartée"):
            st.rerun()


def _carte(app, utilisateur, dossier, numero, p, modifiable):
    with composants.carte():
        nature = "Levier chiffré" if p.type == "levier" else "Piste à étudier"
        st.markdown(f"**{numero} · {nature} · art. {p.article}**  \n{p.titre}")
        st.caption(p.justification)
        if p.gain is not None:
            st.markdown(f"Gain (moteur) : **{formats.montant(p.gain, True)}**")
        else:
            st.caption("Non chiffrée.")
        with st.container(horizontal=True):
            if p.confiance < SEUIL_CONFIANCE:
                composants.badge(f"Confiance faible {p.confiance}", "a_faire")
            else:
                composants.badge(f"Confiance {p.confiance}", "info")
            if p.decision == "acceptee":
                composants.badge("Acceptée", "fait")
            elif p.decision == "ecartee":
                composants.badge("Écartée", "risque")
        with st.expander("Contrôles du juge"):
            for controle in p.controles:
                st.caption(controle)
            if p.motif:
                st.caption(f"Motif : {p.motif}")
        if modifiable and not p.decision:
            with st.container(horizontal=True):
                if st.button("Écarter…", key=f"ecarter_{p.id}", type="tertiary"):
                    _ecarter(app, utilisateur, dossier, p)
                if st.button("Accepter", key=f"accepter_{p.id}", type="primary"):
                    message = "Levier ajouté aux scénarios" if p.type == "levier" else "Piste retenue pour la note"
                    if composants.executer(lambda: app.agent.decider(utilisateur, dossier.id, p.id, True), message):
                        st.rerun()


def afficher(app, utilisateur, dossier, modifiable):
    with composants.carte():
        st.markdown("**Propositions de l'agent**")
        possible, raison = app.agent.peut_utiliser_l_ia(dossier)
        propositions, donnees = app.agent.lister(utilisateur, dossier.id)
        if not possible:
            st.caption(raison)
        elif modifiable:
            libelle = "Relancer l'agent" if propositions else "Demander des propositions"
            if st.button(libelle, icon=":material/lightbulb:", width="stretch"):
                with st.spinner("L'agent analyse le profil pseudonymisé du dossier…"):
                    resultat = composants.executer(lambda: app.agent.demander(utilisateur, dossier.id))
                if resultat is not None:
                    st.rerun()
        for numero, p in enumerate(propositions, 1):
            _carte(app, utilisateur, dossier, numero, p, modifiable)
        if donnees:
            st.caption(f"Proposé par IA, à vérifier · montants recalculés par le moteur · {donnees.get('modele', '')}"
                       f" · profil pseudonymisé · arrêt : {donnees.get('arret', '')}")
            if donnees.get("rejetees"):
                with st.expander(f"{len(donnees['rejetees'])} proposition(s) rejetée(s) par les garde-fous"):
                    for rejet in donnees["rejetees"]:
                        st.caption(rejet)
            with st.expander("Étapes suivies par l'agent"):
                for etape in donnees.get("etapes", []):
                    st.caption(etape)
