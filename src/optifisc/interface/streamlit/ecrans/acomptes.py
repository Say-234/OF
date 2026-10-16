"""E11 — Acomptes d'IS (UC08) : échéancier (art. 51) et décision de demander une réduction (art. 52)."""
from decimal import Decimal

import streamlit as st

from optifisc.interface.streamlit import composants, formats

from . import bandeau_fige, bouton_suite, peut_modifier


def afficher(app, utilisateur, dossier, derniere_balance):
    composants.entete("Acomptes d'IS", "Quatre acomptes de 25 % de l'IS N-1 (art. 51) ; réduction possible sur demande "
                                       "au DGI un mois avant l'échéance (art. 52).")
    bandeau_fige(dossier)
    modifiable = peut_modifier(utilisateur, dossier)
    marge_defaut = app.referentiel.parametres.acomptes.marge_prudence
    marge = st.slider("Marge de prudence ajoutée à l'IS estimé (choix du cabinet)", 0, 30,
                      int(marge_defaut * 100), format="%d %%", key=f"marge_{dossier.id}", disabled=not modifiable,
                      help="Une estimation trop basse de plus de 10 % entraîne une pénalité de 20 % de l'écart "
                           "(art. 52-7).")
    marge_decimal = Decimal(marge) / 100
    ech = app.calcul.echeancier(utilisateur, dossier.id, marge_decimal)

    st.dataframe([{"Échéance": formats.jour(e.date), "Acompte normal (FCFA)": formats.montant(e.montant_normal),
                   "Statut": "payé" if e.payee else "à venir",
                   "Demande de réduction avant le": formats.jour(e.date_limite_demande),
                   "Acompte demandé (FCFA)": formats.montant(ech.recommandation.acompte_demande)
                   if ech.recommandation and not e.payee else "—"} for e in ech.echeances],
                 hide_index=True, alt="Échéancier des acomptes",
                 column_config={"Acompte normal (FCFA)": composants.colonne_montant("Acompte normal (FCFA)"),
                                "Acompte demandé (FCFA)": composants.colonne_montant("Acompte demandé (FCFA)")})
    with st.container(horizontal=True):
        st.metric("IS estimé de l'année", formats.montant(app.calcul.resultat(utilisateur, dossier.id).is_du, True),
                  border=True)
        st.metric("Acomptes prévus", formats.montant(ech.total_normal, True), border=True)
        st.metric("Excédent prévisible", formats.montant(max(ech.excedent_previsible, 0), True), border=True)

    reco = ech.recommandation
    if reco:
        nature = "dispense" if reco.dispense else "réduction"
        st.success(f"Demande de {nature} possible : déposer avant le **{formats.jour(reco.deposer_avant)}** pour "
                   f"l'échéance du {formats.jour(reco.prochaine_echeance)}. Trésorerie préservée : "
                   f"**{formats.montant(reco.tresorerie_preservee, True)}**.", icon=":material/savings:")
        st.caption(reco.risque)
    elif ech.trop_tard:
        st.info(f"Délais dépassés : l'excédent de {formats.montant(ech.credit_impot, True)} deviendra un crédit "
                "d'impôt (art. 51-3).", icon=":material/info:")
    else:
        st.info("Les acomptes ne dépassent pas l'impôt estimé : pas de réduction à demander.", icon=":material/info:")

    decision = app.dependances.donnees.lire(dossier.id, "acomptes")
    if decision is not None:
        composants.badge("Décision enregistrée : demande de réduction" if decision["demande"]
                         else "Décision enregistrée : pas de demande", "fait")
    if modifiable:
        with st.container(horizontal=True, horizontal_alignment="right"):
            if st.button("Pas de demande", icon=":material/block:"):
                if composants.executer(lambda: app.calcul.decider_acomptes(utilisateur, dossier.id, False),
                                       "Décision enregistrée"):
                    st.rerun()
            if reco and st.button("Demander la réduction", type="primary", icon=":material/mail:"):
                if composants.executer(lambda: app.calcul.decider_acomptes(utilisateur, dossier.id, True,
                                                                           marge_decimal), "Décision enregistrée"):
                    st.rerun()
    bouton_suite("livrer", "Étape suivante : livrer")
