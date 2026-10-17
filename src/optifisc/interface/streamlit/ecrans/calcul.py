"""E09 — Calcul de l'IS prévisionnel (UC07) : tableau de passage, régime, seuil de bascule, piste d'audit."""
import streamlit as st

from optifisc.domaine.balance import Niveau
from optifisc.domaine.dossier import EtatDossier
from optifisc.interface.streamlit import composants, formats, graphiques

from . import bandeau_fige, bouton_suite, peut_modifier


def afficher(app, utilisateur, dossier, derniere_balance):
    actions = composants.entete("Calcul de l'impôt", "IS de droit commun (art. 46) comparé au minimum de "
                                                     "perception (art. 47) ; le plus élevé est dû.")
    with actions:
        if dossier.etat is EtatDossier.EN_PREPARATION and peut_modifier(utilisateur, dossier):
            if st.button("Calculer", type="primary", icon=":material/calculate:"):
                if composants.executer(lambda: app.calcul.calculer(utilisateur, dossier.id), "Calcul effectué"):
                    st.rerun()
    bandeau_fige(dossier)
    if dossier.etat is EtatDossier.EN_PREPARATION:
        st.warning("Le calcul n'est pas à jour : des données ont été saisies ou modifiées. Cliquez sur « Calculer ».",
                   icon=":material/sync_problem:")
    r = app.calcul.resultat(utilisateur, dossier.id)

    with st.container(horizontal=True):
        st.metric("IS de droit commun", formats.montant(r.is_droit_commun, unite=True), border=True,
                  help=f"{formats.pourcentage(r.taux_is)} × résultat fiscal positif")
        st.metric("Minimum de perception", formats.montant(r.minimum_perception, unite=True), border=True,
                  help=f"{formats.pourcentage(r.taux_minimum)} des produits encaissables, plancher inclus")
        st.metric("IS dû", formats.montant(r.is_du, unite=True), border=True, help=f"Régime : {r.regime}")

    with composants.carte():
        st.markdown("**Du résultat comptable au résultat fiscal**")
        st.altair_chart(graphiques.passage_resultat(r.resultat_comptable, r.reintegrations, r.deductions,
                                                    r.deficit_impute, r.resultat_fiscal),
                        alt="Cascade du résultat comptable au résultat fiscal")
    st.subheader("Tableau de passage", anchor=False)
    passage = [
        ("A", "Résultat comptable projeté au 31/12", "SYSCOHADA", r.resultat_comptable),
        ("B", "Réintégrations", "art. 15 à 43", r.reintegrations),
        ("C", "Déductions", "art. 15 à 43", r.deductions),
        ("D", "Déficits antérieurs imputés", "art. 43", r.deficit_impute),
        ("E", "Résultat fiscal (A + B − C − D)", "", r.resultat_fiscal),
        ("F", f"IS de droit commun ({formats.pourcentage(r.taux_is)})", "art. 46", r.is_droit_commun),
        ("G", f"Minimum de perception ({formats.pourcentage(r.taux_minimum)} de "
              f"{formats.montant(r.produits_encaissables)})", "art. 47", r.minimum_perception),
        ("H", f"IS dû — {r.regime}", "art. 46-47", r.is_du),
        ("I", "Redevance ORTB", "art. 47-6", r.redevance_ortb),
        ("J", "Total à acquitter (H + I)", "", r.impot_total),
    ]
    st.dataframe([{"Réf.": ref, "Libellé": lib, "Article": art, "Montant (FCFA)": formats.montant(m)}
                  for ref, lib, art, m in passage], hide_index=True,
                 column_config={"Montant (FCFA)": composants.colonne_montant("Montant (FCFA)")},
                 alt="Tableau de passage du résultat comptable à l'impôt")
    st.caption(f"Seuil de bascule : au-delà d'un résultat fiscal de {formats.montant(r.seuil_bascule, unite=True)}, "
               "l'IS de droit commun dépasse le minimum de perception.")

    for alerte in r.alertes:
        (st.warning if alerte.niveau is Niveau.ATTENTION else st.info)(alerte.message, icon=":material/info:")

    with st.expander("Piste d'audit : chaque montant avec sa règle, son article et sa formule"):
        st.dataframe([{"Étape": a.etape, "Référence": a.reference, "Libellé": a.libelle, "Article": a.article,
                       "Base (FCFA)": formats.montant(a.base), "Montant (FCFA)": formats.montant(a.montant),
                       "Détail": a.detail} for a in r.audit], hide_index=True,
                     column_config={"Base (FCFA)": composants.colonne_montant("Base (FCFA)"),
                                    "Montant (FCFA)": composants.colonne_montant("Montant (FCFA)")},
                     alt="Piste d'audit du calcul")
        st.caption(f"Version du référentiel : {r.version_referentiel}")

    bouton_suite("leviers", "Étape suivante : leviers avant clôture")
