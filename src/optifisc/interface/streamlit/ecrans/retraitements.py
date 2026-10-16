"""E08 — Retraitements (UC02) : schéma maître-détail. Le tableau liste les 28 règles ; la ligne choisie
s'affiche dessous, avec la saisie (montant ou « néant ») pour les règles qui la demandent."""
from decimal import Decimal

import streamlit as st

from optifisc.domaine.referentiel import Sens
from optifisc.interface.streamlit import composants, formats

from . import bandeau_fige, bouton_suite, peut_modifier


def _statut(ligne) -> str:
    return "✓ renseignée" if ligne.renseignee else "▲ à compléter"


def _saisie(app, utilisateur, dossier, cle_regle, valeur_actuelle, modifiable):
    """Saisie d'un montant ou de « néant » pour une règle (ou une sanction) à saisie."""
    montant, valide = composants.champ_montant("Montant", f"saisie_{dossier.id}_{cle_regle}", valeur_actuelle,
                                               desactive=not modifiable)
    if not modifiable:
        return
    with st.container(horizontal=True):
        if st.button("Enregistrer", type="primary", key=f"ok_{cle_regle}", disabled=not valide or montant is None):
            if composants.executer(lambda: app.dossiers.saisir(utilisateur, dossier.id, cle_regle, montant),
                                   "Saisie enregistrée"):
                st.rerun()
        if st.button("Néant", key=f"neant_{cle_regle}", help="Rien à retraiter pour cette règle (0 FCFA)."):
            if composants.executer(lambda: app.dossiers.saisir(utilisateur, dossier.id, cle_regle, Decimal(0)),
                                   "Néant enregistré"):
                st.rerun()
        if valeur_actuelle is not None and st.button("Effacer la réponse", key=f"effacer_{cle_regle}",
                                                     type="tertiary"):
            if composants.executer(lambda: app.dossiers.saisir(utilisateur, dossier.id, cle_regle, None)):
                st.rerun()


def afficher(app, utilisateur, dossier, derniere_balance):
    resultat = app.calcul.resultat(utilisateur, dossier.id)
    ref = app.referentiel
    manquantes = len(resultat.saisies_manquantes)
    actions = composants.entete("Retraitements",
                                "Passage du résultat comptable au résultat fiscal (CGI art. 15 à 43).")
    with actions:
        if manquantes:
            composants.badge(f"{manquantes} saisie(s) à compléter sur {len(resultat.retraitements)}", "a_faire")
        else:
            composants.badge("Toutes les règles sont renseignées", "fait")
    bandeau_fige(dossier)
    modifiable = peut_modifier(utilisateur, dossier)
    validees = app.validation.regles_validees()
    if app.mode == "demo" and modifiable and manquantes:
        with st.container(horizontal=True, vertical_alignment="center"):
            st.caption(":material/science: Démonstration : répondre « néant » à toutes les saisies restantes "
                       "(en cabinet, chaque règle s'examine une par une).")
            if st.button(f"Tout mettre à néant ({manquantes})", icon=":material/done_all:"):
                if composants.executer(lambda: app.dossiers.saisir_neant_restantes(utilisateur, dossier.id),
                                       "Saisies restantes mises à néant"):
                    st.rerun()

    categories = {"toutes": "Toutes", **{c.id: c.court for c in ref.categories}}
    with st.container(horizontal=True, vertical_alignment="center"):
        filtre = st.segmented_control("Catégorie", list(categories), format_func=categories.get, default="toutes",
                                      required=True, label_visibility="collapsed", key=f"cat_{dossier.id}")
        a_completer = st.toggle("Seulement à compléter", key=f"acomp_{dossier.id}")
    lignes = [li for li in resultat.retraitements
              if (filtre == "toutes" or li.categorie == filtre) and (not a_completer or not li.renseignee)]
    tableau = [{"Réf.": li.id_regle.split("_")[0], "Règle": li.libelle, "Article": li.article.replace("CGI ", ""),
                "Origine": "Saisie" if li.depuis_saisie else "Balance",
                "Base (FCFA)": formats.montant(li.base) if li.renseignee else "—",
                "Retenu (FCFA)": formats.montant(li.montant) if li.renseignee else "—",
                "Sens": "+" if li.sens is Sens.REINTEGRATION else "−", "Statut": _statut(li),
                "Règle validée": "✓" if li.id_regle in validees else "à valider"}
               for li in lignes]
    evenement = st.dataframe(tableau, hide_index=True, on_select="rerun", selection_mode="single-row",
                             key=f"tableau_retraitements_{dossier.id}_{filtre}_{a_completer}",
                             column_config={"Base (FCFA)": composants.colonne_montant("Base (FCFA)"),
                                            "Retenu (FCFA)": composants.colonne_montant("Retenu (FCFA)"),
                                            "Règle": st.column_config.TextColumn(width="large"),
                                            "Sens": st.column_config.TextColumn(width="small")},
                             alt="Règles de retraitement")
    with st.container(horizontal=True, horizontal_alignment="right"):
        st.markdown(f"Total réintégrations **{formats.montant(resultat.reintegrations, unite=True)}** · "
                    f"Total déductions **{formats.montant(resultat.deductions, unite=True)}**")

    if evenement.selection.rows:
        ligne = lignes[evenement.selection.rows[0]]
        regle = ref.regle(ligne.id_regle)
        with st.container(border=True):
            st.markdown(f"**{regle.id.split('_')[0]} — {regle.libelle}**")
            st.caption(f"{regle.article} · " + ("règle validée par le cabinet" if regle.id in validees
                                                else "règle à valider par le cabinet"))
            if regle.explication:
                st.write(regle.explication)
            if regle.ou_trouver:
                st.markdown(f":material/search: **Où trouver l'information :** {regle.ou_trouver}")
            if ligne.renseignee:
                st.caption(f"Calcul : {ligne.detail}")
            if regle.est_saisie:
                _saisie(app, utilisateur, dossier, regle.id, dossier.saisies.get(regle.id), modifiable)
    else:
        st.caption("Sélectionnez une ligne pour voir le détail du calcul et, le cas échéant, saisir le montant.")

    if ref.sanctions:
        st.subheader("Hors résultat fiscal", anchor=False)
        for sanction in ref.sanctions:
            with st.container(border=True):
                st.markdown(f"**{sanction.libelle}** · {sanction.article}")
                st.caption(sanction.explication)
                _saisie(app, utilisateur, dossier, sanction.id, dossier.saisies.get(sanction.id), modifiable)
        for cout in resultat.hors_resultat:
            st.warning(f"Droit de timbre : {formats.montant(cout.montant, unite=True)} ({cout.article}).",
                       icon=":material/receipt_long:")

    bouton_suite("calcul", "Étape suivante : calcul de l'impôt")
