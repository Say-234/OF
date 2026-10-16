"""E03 — Tableau de bord : la liste des dossiers en TABLEAU triable (doc 05, B) ; E04 — création (UC05)."""
import streamlit as st

from optifisc.application.autorisation import peut
from optifisc.domaine.dossier import CategorieTaux, EtatDossier, Secteur
from optifisc.domaine.utilisateur import Role
from optifisc.interface.streamlit import composants, etat, formats

app = etat.application()
utilisateur = etat.utilisateur()
param = app.referentiel.parametres


@st.dialog("Nouveau dossier", width="medium")
def nouveau_dossier():
    with st.form("nouveau_dossier", border=False):
        raison = st.text_input("Raison sociale", max_chars=120)
        secteur = st.selectbox("Secteur (minimum de perception, art. 47)", list(Secteur),
                               format_func=lambda s: param.libelles_secteur[s.value])
        categorie = st.selectbox("Taux de l'IS (art. 46)", list(CategorieTaux),
                                 format_func=lambda c: param.libelles_taux[c.value])
        st.text_input("Exercice", value=str(app.referentiel.millesime), disabled=True)
        demonstration = st.checkbox("Dossier de démonstration (données fictives)", value=app.mode == "demo",
                                    help="Seuls les dossiers de démonstration peuvent utiliser l'IA en ligne "
                                         "par défaut (doc 01, A.3).")
        if st.form_submit_button("Créer le dossier", type="primary"):
            dossier = composants.executer(lambda: app.dossiers.creer(
                utilisateur, raison, secteur, categorie, app.referentiel.millesime, demonstration))
            if dossier:
                etat.ouvrir_dossier(dossier.id, "balance")
                st.switch_page("app_pages/dossier.py")


actions = composants.entete("Dossiers", f"Dossiers IS de l'exercice {app.referentiel.millesime}. "
                                        "Cliquez sur une ligne pour ouvrir le dossier.")
if peut(utilisateur, "creer_dossier"):
    if actions.button("Nouveau dossier", icon=":material/add:", type="primary"):
        nouveau_dossier()

resumes = app.dossiers.lister(utilisateur)
if not resumes:
    composants.vide("Aucun dossier pour le moment. Créez le premier avec « Nouveau dossier ».")
    composants.pied_de_page()
    st.stop()

compte = {e: sum(r.dossier.etat is e for r in resumes) for e in EtatDossier}
groupes = {"À valider": {EtatDossier.A_VALIDER},
           "En préparation": {EtatDossier.BROUILLON, EtatDossier.EN_PREPARATION, EtatDossier.CALCULE},
           "Validés et livrés": {EtatDossier.VALIDE, EtatDossier.LIVRE}}
filtres = {f"Tous ({len(resumes)})": None,
           **{f"{nom} ({sum(compte[e] for e in etats)})": etats for nom, etats in groupes.items()}}
with st.container(horizontal=True, vertical_alignment="bottom"):
    choix = st.segmented_control("Filtrer par état", list(filtres), default=list(filtres)[0], required=True,
                                 label_visibility="collapsed")
    recherche = st.text_input("Rechercher un client", placeholder="Rechercher un client",
                              label_visibility="collapsed", icon=":material/search:", width=280)

visibles = [r for r in resumes
            if (filtres.get(choix) is None or r.dossier.etat in filtres[choix])
            and recherche.lower() in r.dossier.raison_sociale.lower()]
lignes = [{
    "Client": r.dossier.raison_sociale,
    "Secteur": param.libelles_secteur[r.dossier.secteur.value].split(" (")[0],
    "Arrêté": formats.jour(r.date_arrete),
    "IS prévisionnel (FCFA)": formats.montant(r.is_du) if r.is_du is not None else "—",
    "Régime": r.regime or "—",
    "État": composants.ETATS[r.dossier.etat][0],
    "Avancement": r.etapes_faites,
    "Prochaine échéance": r.prochaine_echeance or "—",
    **({} if utilisateur.role is Role.COLLABORATEUR else {"Responsable": composants.nom(app, r.dossier.responsable)}),
} for r in visibles]
# Clé renouvelée après chaque ouverture : sinon la ligne resterait sélectionnée au retour sur cette page.
generation = st.session_state.setdefault("generation_tableau_dossiers", 0)
colonne_is = "IS prévisionnel (FCFA)"
evenement = st.dataframe(lignes, hide_index=True, on_select="rerun", selection_mode="single-row",
                         key=f"tableau_dossiers_{generation}", alt="Liste des dossiers",
                         column_config={colonne_is: composants.colonne_montant(colonne_is),
                                        "Arrêté": st.column_config.TextColumn(width="small"),
                                        "Prochaine échéance": st.column_config.TextColumn(width="large"),
                                        "Avancement": st.column_config.ProgressColumn(
                                            "Avancement", min_value=0, max_value=7, format="%d / 7 étapes")})
if evenement.selection.rows:
    st.session_state["generation_tableau_dossiers"] = generation + 1
    etat.ouvrir_dossier(visibles[evenement.selection.rows[0]].dossier.id)
    st.switch_page("app_pages/dossier.py")

composants.pied_de_page()
