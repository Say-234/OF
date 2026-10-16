"""E12-E13 — Soumission, validation et livrables (UC04)."""
import streamlit as st

from optifisc.application.autorisation import peut
from optifisc.domaine.dossier import EtatDossier
from optifisc.interface.streamlit import composants

from .synthese import dialogue_valider


def _livrables(app, utilisateur, dossier, definitif: bool):
    cle = f"livrables_{dossier.id}_{'def' if definitif else 'prov'}"
    libelle = "Générer les livrables définitifs" if definitif else "Générer les livrables provisoires (projet)"
    if st.button(libelle, type="primary" if definitif else "secondary", icon=":material/description:", key=f"b_{cle}"):
        fichiers = composants.executer(lambda: app.livrables.generer(utilisateur, dossier.id, definitif),
                                       "Livrables générés")
        if fichiers:
            st.session_state[cle] = fichiers         # fichiers à télécharger (pas un résultat de calcul)
            st.rerun()
    for fichier in st.session_state.get(cle, []):
        st.download_button(fichier.nom, fichier.contenu, file_name=fichier.nom, mime=fichier.type_mime,
                           icon=":material/download:", key=f"d_{cle}_{fichier.nom}", on_click="ignore")


def afficher(app, utilisateur, dossier, derniere_balance):
    composants.entete("Livrer", "Soumettre le dossier à l'expert-comptable, puis produire la note de pilotage, le "
                                "dossier de calcul et, le cas échéant, la lettre au DGI.")
    st.subheader("Liste de contrôle avant soumission", anchor=False)
    for point in app.validation.liste_de_controle(dossier):
        composants.badge(point.libelle, "fait" if point.respecte else "a_faire")

    if dossier.etat is EtatDossier.CALCULE and peut(utilisateur, "soumettre_dossier", dossier):
        if st.button("Soumettre à l'expert-comptable", type="primary", icon=":material/send:"):
            if composants.executer(lambda: app.validation.soumettre(utilisateur, dossier.id), "Dossier soumis"):
                st.rerun()
    elif dossier.etat is EtatDossier.EN_PREPARATION:
        st.caption("Recalculez l'impôt (étape 4) avant de soumettre.")
    elif dossier.etat is EtatDossier.A_VALIDER:
        st.info("Dossier soumis : en attente de la validation de l'expert-comptable.", icon=":material/pending:")
        if peut(utilisateur, "valider_dossier", dossier):
            resultat = app.calcul.resultat(utilisateur, dossier.id)
            if st.button("Valider le dossier", type="primary", icon=":material/verified:"):
                dialogue_valider(app, utilisateur, dossier, app.validation.regles_non_validees_utilisees(resultat))
    else:
        fige = app.dependances.donnees.lire(dossier.id, "resultat_fige") or {}
        if fige:
            mention = " — préparé et validé par la même personne" if fige.get("meme_personne") else ""
            st.success(f"Validé par {fige['valide_par']} le {fige['valide_le'][:10]}{mention}.",
                       icon=":material/verified:")

    st.subheader("Livrables", anchor=False)
    if peut(utilisateur, "livrables_provisoires", dossier):
        _livrables(app, utilisateur, dossier, definitif=False)
    if dossier.etat in (EtatDossier.VALIDE, EtatDossier.LIVRE) and peut(utilisateur, "livrables_definitifs", dossier):
        _livrables(app, utilisateur, dossier, definitif=True)
    elif not peut(utilisateur, "livrables_definitifs", dossier):
        st.caption("Les livrables définitifs sont générés par l'expert-comptable après validation.")
