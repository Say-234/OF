"""E05 — Synthèse du dossier : 3 indicateurs, points d'attention, derniers événements, décision de l'expert."""
import streamlit as st

from optifisc.application.autorisation import peut
from optifisc.domaine.balance import Niveau
from optifisc.domaine.dossier import EtatDossier
from optifisc.interface.streamlit import composants, etat, formats


@st.dialog("Valider le dossier")
def dialogue_valider(app, utilisateur, dossier, non_validees):
    st.write("La validation fige le résultat : montants, version du référentiel, date et nom du valideur.")
    verifiees = True
    if non_validees:
        st.warning("Règles utilisées encore « à valider » par le cabinet : "
                   f"{', '.join(r.split('_')[0] for r in non_validees)}.",
                   icon=":material/rule:")
        verifiees = st.checkbox("J'ai vérifié les règles non validées utilisées dans ce calcul")
    if st.button("Valider le dossier", type="primary", disabled=not verifiees):
        if composants.executer(lambda: app.validation.valider(utilisateur, dossier.id, verifiees),
                               "Dossier validé"):
            st.rerun()


@st.dialog("Renvoyer le dossier au collaborateur")
def _renvoyer(app, utilisateur, dossier):
    commentaire = st.text_area("Commentaire (obligatoire)", placeholder="Ce qui doit être revu…")
    if st.button("Renvoyer", type="primary"):
        if composants.executer(lambda: app.validation.renvoyer(utilisateur, dossier.id, commentaire),
                               "Dossier renvoyé en préparation"):
            st.rerun()


@st.dialog("Rouvrir le dossier")
def _rouvrir(app, utilisateur, dossier):
    motif = st.text_area("Motif de la réouverture (obligatoire)")
    if st.button("Rouvrir", type="primary"):
        if composants.executer(lambda: app.validation.rouvrir(utilisateur, dossier.id, motif), "Dossier rouvert"):
            st.rerun()


def afficher(app, utilisateur, dossier, derniere_balance):
    if derniere_balance is None:
        composants.vide("Commencez par importer la balance du client (étape 1).")
        st.button("Importer la balance", type="primary", icon=":material/upload_file:",
                  on_click=etat.aller_a_l_etape, args=("balance",))
        return
    resultat = app.calcul.resultat(utilisateur, dossier.id)
    retenu = app.scenarios.scenario_retenu(dossier.id)

    with st.container(horizontal=True):
        st.metric("Résultat fiscal", formats.montant(resultat.resultat_fiscal, unite=True), border=True,
                  help="Résultat comptable projeté + réintégrations − déductions − déficits imputés")
        st.metric("IS dû", formats.montant(resultat.is_du, unite=True), border=True,
                  help=f"Régime : {resultat.regime} (art. 46-47)")
        st.metric("Gain du scénario retenu", formats.montant(retenu.gain_is, unite=True) if retenu else "—",
                  border=True, help=f"Scénario {retenu.nom}" if retenu else "Aucun scénario retenu")

    # Points d'attention regroupés dans un seul cadre (une ligne chacun) plutôt qu'une pile d'encadrés colorés
    non_validees = app.validation.regles_non_validees_utilisees(resultat)
    renvoi = app.dependances.donnees.lire(dossier.id, "renvoi")
    points = []
    if renvoi and dossier.etat is EtatDossier.EN_PREPARATION:
        points.append(("risque", f"Renvoyé par {composants.nom(app, renvoi['par'])} : {renvoi['commentaire']}"))
    if non_validees:
        references = ", ".join(r.split("_")[0] for r in non_validees)
        points.append(("a_faire", f"{len(non_validees)} règle(s) encore « à valider » par le cabinet utilisées : "
                                  f"{references}"))
    for alerte in resultat.alertes:
        points.append(("a_faire" if alerte.niveau is Niveau.ATTENTION else "info", alerte.message))
    ech = app.calcul.echeancier(utilisateur, dossier.id)
    if ech.recommandation:
        points.append(("info", f"Réduction d'acompte possible : demande à déposer avant le "
                               f"{formats.jour(ech.recommandation.deposer_avant)}"))
    gauche, droite = st.columns([3, 2], gap="medium")
    with gauche:
        composants.liste_de_points(points or [("fait", "Aucun point d'attention")], "Points d'attention")
    with droite:
        with st.container(border=True):
            st.markdown("**Derniers événements**")
            for evenement in app.dossiers.journal(utilisateur, dossier.id, 4):
                st.caption(f"{formats.horodatage(evenement.quand)} · {composants.nom(app, evenement.utilisateur)}"
                           f"  \n{composants.action(evenement.action)}")
            st.page_link("app_pages/journal.py", label="Journal complet", icon=":material/history:")

    if dossier.etat is EtatDossier.A_VALIDER and peut(utilisateur, "valider_dossier", dossier):
        with st.container(horizontal=True, horizontal_alignment="right"):
            if st.button("Renvoyer avec commentaire", icon=":material/reply:"):
                _renvoyer(app, utilisateur, dossier)
            if st.button("Valider le dossier", type="primary", icon=":material/verified:"):
                dialogue_valider(app, utilisateur, dossier, non_validees)
    elif dossier.etat in (EtatDossier.VALIDE, EtatDossier.LIVRE) and peut(utilisateur, "rouvrir_dossier", dossier):
        with st.container(horizontal=True, horizontal_alignment="right"):
            if st.button("Rouvrir le dossier", icon=":material/lock_open:"):
                _rouvrir(app, utilisateur, dossier)
