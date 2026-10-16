"""E06 — Balance : import en deux temps, aperçu (rapport de lecture et contrôles) puis confirmation (UC01)."""
from datetime import date

import streamlit as st

from optifisc.domaine.balance import Niveau, controler
from optifisc.interface.streamlit import composants, formats

from . import bandeau_fige, bouton_suite, peut_modifier

ALERTES = {Niveau.ERREUR: (st.error, ":material/error:"), Niveau.ATTENTION: (st.warning, ":material/warning:"),
           Niveau.INFO: (st.info, ":material/info:")}


def _afficher_rapport(apercu_ou_balance, rapport, controles):
    for controle in controles:
        fonction, icone = ALERTES[controle.niveau]
        fonction(controle.message, icon=icone)
    colonnes = ", ".join(f"{role} : « {libelle} »" for role, libelle in rapport.colonnes.items())
    st.table({"Fichier": f"{rapport.fichier} {('· feuille ' + rapport.feuille) if rapport.feuille else ''}",
              "En-tête": f"ligne {rapport.ligne_entete}",
              "Montants lus dans": rapport.base,
              "Colonnes": colonnes,
              "Comptes lus": str(len(apercu_ou_balance.lignes)),
              "Lignes de total ignorées": str(rapport.lignes_totaux_ignorees),
              "Regroupements ignorés": ", ".join(rapport.regroupements_ignores) or "aucun"},
             border="horizontal", width="content")
    with st.expander(f"Voir les {len(apercu_ou_balance.lignes)} comptes lus"):
        st.dataframe([{"Compte": li.compte, "Intitulé": li.libelle, "Débit": formats.montant(li.debit),
                       "Crédit": formats.montant(li.credit)} for li in apercu_ou_balance.lignes],
                     hide_index=True, column_config={"Débit": composants.colonne_montant("Débit"),
                                                     "Crédit": composants.colonne_montant("Crédit")},
                     alt="Comptes lus dans la balance")


def afficher(app, utilisateur, dossier, derniere_balance):
    composants.entete("Balance", "Importer la balance générale arrêtée à date, telle qu'exportée du logiciel "
                                 "comptable (Excel ou CSV).")
    bandeau_fige(dossier)
    if derniere_balance:
        balance, rapport, date_arrete = derniere_balance
        st.success(f"Balance enregistrée : arrêtée au {formats.jour(date_arrete)}, {len(balance.lignes)} comptes.",
                   icon=":material/check_circle:")
        with st.expander("Rapport de lecture de la balance enregistrée"):
            _afficher_rapport(balance, rapport, controler(balance, rapport))
    if not peut_modifier(utilisateur, dossier):
        if derniere_balance:
            bouton_suite("hypotheses", "Étape suivante : hypothèses")
        return

    st.subheader("Remplacer la balance" if derniere_balance else "Importer la balance", anchor=False)
    generation = st.session_state.setdefault(f"import_{dossier.id}", 0)
    with st.container(horizontal=True, vertical_alignment="bottom"):
        fichier = st.file_uploader("Fichier de balance", type=["xlsx", "xls", "csv", "txt"],
                                   key=f"fichier_{dossier.id}_{generation}")
        arrete = st.date_input("Date d'arrêté", value=date(dossier.exercice, 6, 30), format="DD/MM/YYYY",
                               min_value=date(dossier.exercice, 1, 31), max_value=date(dossier.exercice, 12, 31),
                               width=200, key=f"arrete_{dossier.id}")
    if fichier is None:
        st.caption("Formats reconnus : 4 colonnes (compte, intitulé, débit, crédit), solde signé, ou 6 à 8 colonnes "
                   "(à-nouveaux, mouvements, soldes). Les titres, totaux et comptes de regroupement sont ignorés.")
        if derniere_balance:
            bouton_suite("hypotheses", "Étape suivante : hypothèses")
        return

    apercu = composants.executer(lambda: app.balance.apercu(utilisateur, dossier.id, fichier.getvalue(),
                                                            fichier.name, arrete))
    if apercu is None:
        return
    st.markdown("**Aperçu — rien n'est encore enregistré.** Vérifiez le rapport de lecture, puis confirmez.")
    _afficher_rapport(apercu.balance, apercu.rapport, apercu.controles)
    if derniere_balance:
        st.warning("Confirmer remplacera la balance actuelle (l'ancienne reste dans l'historique).",
                   icon=":material/swap_horiz:")
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Confirmer l'import", type="primary", icon=":material/check:"):
            if composants.executer(lambda: app.balance.confirmer(utilisateur, dossier.id, apercu),
                                   "Balance enregistrée"):
                st.session_state[f"import_{dossier.id}"] = generation + 1
                st.rerun()
