"""E10 — Leviers avant clôture (UC03) et panneau de l'agent IA (UC14).

À gauche : paramétrer des leviers, voir l'effet AVANT / APRÈS calculé par le moteur, enregistrer jusqu'à
3 scénarios et en retenir un. À droite : les propositions de l'agent, séparées visuellement (doc 05, D5.8).
"""
import streamlit as st

from optifisc.domaine.moteur.leviers import dons_deja_comptabilises, marge_dons
from optifisc.domaine.scenario import LevierChoisi
from optifisc.interface.streamlit import composants, formats

from . import agent as panneau_agent
from . import bandeau_fige, bouton_suite, peut_modifier

SIMULABLES = ("L01_INVESTISSEMENT_DEGRESSIF", "L02_AMORTISSEMENT_ACCELERE", "L03_PROVISION_JUSTIFIEE",
              "L04_DONS_PLAFOND", "L05_CHARGES_ANTICIPEES")


def _brouillon(dossier_id: str) -> list[dict]:
    """Leviers en cours de paramétrage (saisies de l'utilisateur, pas des résultats de calcul)."""
    return st.session_state.setdefault(f"brouillon_leviers_{dossier_id}", [])


def _formulaire(app, dossier, resultat, levier):
    """Paramètres d'un levier et ses conditions légales. Renvoie les paramètres saisis, ou None si invalides."""
    p = {}
    cle = f"{dossier.id}_{levier.id}"
    with st.container(border=True):
        st.markdown(f"**{levier.libelle}** · {levier.article}")
        st.caption(levier.effet)
        montant, valide = composants.champ_montant("Montant HT" if levier.id in SIMULABLES[:2] else "Montant",
                                                   f"montant_{cle}")
        p["montant"] = str(montant) if montant is not None else ""
        if levier.id in SIMULABLES[:2]:
            colonnes = st.columns(2)
            p["duree"] = colonnes[0].number_input("Durée d'utilisation (ans)", 1, 30, 5, key=f"duree_{cle}")
            p["mois_acquisition"] = colonnes[1].selectbox(
                "Mois d'acquisition", range(1, 13), index=min(11, app.dependances.horloge.aujourd_hui().month),
                format_func=lambda m: formats.MOIS[m - 1], key=f"mois_{cle}")
        st.markdown("Conditions légales")
        if levier.id in SIMULABLES[:2]:
            p["neuf"] = st.checkbox("Matériel acquis à l'état neuf", value=True, key=f"neuf_{cle}")
        if levier.id == "L02_AMORTISSEMENT_ACCELERE":
            p["usage_exclusif"] = st.checkbox("Usage exclusif : fabrication, manutention, hôtellerie, téléphonie, "
                                              "transport ou exploitation agricole", value=True, key=f"usage_{cle}")
        if levier.id == "L03_PROVISION_JUSTIFIEE":
            p["justifiee"] = st.checkbox("Perte ou charge nettement précisée et probable, née dans l'exercice",
                                         key=f"just_{cle}")
            p["au_releve"] = st.checkbox("Portée au relevé des provisions", key=f"releve_{cle}")
        if levier.id == "L04_DONS_PLAFOND":
            p["vers_etat"] = st.checkbox("Don à l'État ou à ses démembrements (éducation, santé, culture…)",
                                         key=f"etat_{cle}")
            deja = dons_deja_comptabilises(app.referentiel, resultat.balance_projetee)
            marge = marge_dons(app.referentiel, deja, resultat.chiffre_affaires, p["vers_etat"])
            st.caption(f"Dons déjà comptabilisés : {formats.montant(deja, True)} · marge de plafond : "
                       f"{formats.montant(marge, True)}")
        if levier.id == "L05_CHARGES_ANTICIPEES":
            p["nature"] = st.text_input("Nature de la dépense", value="Formation du personnel", key=f"nature_{cle}")
            p["especes"] = st.checkbox("Règlement en espèces", key=f"especes_{cle}")
        with st.expander("Conditions du CGI"):
            for condition in levier.conditions:
                st.markdown(f"- {condition}")
    return p if valide and montant else None


def afficher(app, utilisateur, dossier, derniere_balance):
    composants.entete("Leviers avant clôture",
                      f"Chiffrer les options légales encore ouvertes avant le 31/12/{dossier.exercice}.")
    bandeau_fige(dossier)
    modifiable = peut_modifier(utilisateur, dossier)
    resultat = app.calcul.resultat(utilisateur, dossier.id)
    st.markdown(f"**Position de départ** · IS de droit commun {formats.montant(resultat.is_droit_commun, True)} · "
                f"minimum de perception {formats.montant(resultat.minimum_perception, True)} · seuil de bascule "
                f"{formats.montant(resultat.seuil_bascule, True)}")
    if resultat.au_minimum:
        st.info("Le minimum de perception s'applique : réduire le résultat ne réduit pas l'impôt cette année. "
                "Les leviers utiles sont la trésorerie (acomptes).", icon=":material/info:")

    gauche, droite = st.columns([2, 1], gap="large")
    with gauche:
        brouillon = _brouillon(dossier.id)
        if modifiable:
            leviers = [app.referentiel.levier(i) for i in SIMULABLES]
            choisi = st.selectbox("Levier à paramétrer", leviers, format_func=lambda lv: f"{lv.id[:3]} — {lv.libelle}",
                                  key=f"choix_levier_{dossier.id}")
            parametres = _formulaire(app, dossier, resultat, choisi)
            if st.button("Ajouter au scénario en cours", icon=":material/add:", disabled=parametres is None):
                brouillon[:] = [b for b in brouillon if b["id_levier"] != choisi.id]
                brouillon.append({"id_levier": choisi.id, "parametres": parametres})
                st.rerun()

        if brouillon:
            st.subheader("Scénario en cours", anchor=False)
            choix = [LevierChoisi(b["id_levier"], b["parametres"]) for b in brouillon]
            simulation = composants.executer(lambda: app.scenarios.simuler(utilisateur, dossier.id, choix))
            effets = composants.executer(lambda: app.scenarios.effets(utilisateur, dossier.id, choix)) or []
            for effet in effets:
                with st.container(border=True):
                    with st.container(horizontal=True, vertical_alignment="center"):
                        st.markdown(f"**{effet.libelle}** · {effet.article}")
                        if effet.bloquant:
                            composants.badge("Conditions non remplies", "risque")
                        if modifiable and st.button("Retirer", key=f"retirer_{effet.id_levier}", type="tertiary"):
                            brouillon[:] = [b for b in brouillon if b["id_levier"] != effet.id_levier]
                            st.rerun()
                    for message in effet.conformite:
                        st.caption(message)
            if simulation:
                st.dataframe([
                    {"": "Résultat fiscal", "Avant (FCFA)": formats.montant(simulation.reference.resultat_fiscal),
                     "Après (FCFA)": formats.montant(simulation.simulation.resultat_fiscal)},
                    {"": "IS dû", "Avant (FCFA)": formats.montant(simulation.reference.is_du),
                     "Après (FCFA)": formats.montant(simulation.simulation.is_du)},
                    {"": "Gain d'IS", "Avant (FCFA)": "", "Après (FCFA)": formats.montant(simulation.gain_is)},
                    {"": "Décaissement", "Avant (FCFA)": "", "Après (FCFA)": formats.montant(simulation.decaissement)},
                ], hide_index=True, column_config={"Avant (FCFA)": composants.colonne_montant("Avant (FCFA)"),
                                                   "Après (FCFA)": composants.colonne_montant("Après (FCFA)")},
                    alt="Comparaison avant et après les leviers")
                for texte in simulation.lecture:
                    st.info(texte, icon=":material/lightbulb:")
            if modifiable and st.button("Enregistrer comme scénario", type="primary", icon=":material/save:"):
                if composants.executer(lambda: app.scenarios.enregistrer(utilisateur, dossier.id, choix),
                                       "Scénario enregistré"):
                    brouillon.clear()
                    st.rerun()

        st.subheader("Scénarios enregistrés", anchor=False)
        scenarios = app.scenarios.lister(utilisateur, dossier.id)
        decision = app.dependances.donnees.lire(dossier.id, "decision_leviers")
        if not scenarios:
            st.caption("Aucun scénario enregistré (3 au plus).")
        for s in scenarios:
            with st.container(border=True, horizontal=True, vertical_alignment="center"):
                st.markdown(f"**Scénario {s.nom}** · {', '.join(lv.id_levier[:3] for lv in s.leviers)} · gain "
                            f"{formats.montant(s.gain_is, True)}")
                if s.retenu:
                    composants.badge("Retenu", "fait")
                elif modifiable and st.button("Retenir", key=f"retenir_{s.id}"):
                    if composants.executer(lambda s=s: app.scenarios.retenir(utilisateur, dossier.id, s.id)):
                        st.rerun()
                if modifiable and st.button("Supprimer", key=f"suppr_{s.id}", type="tertiary"):
                    if composants.executer(lambda s=s: app.scenarios.supprimer(utilisateur, dossier.id, s.id)):
                        st.rerun()
        if decision is not None and not decision.get("scenario_id"):
            composants.badge("Décision enregistrée : aucun levier retenu", "info")
        if modifiable and st.button("Aucun levier retenu", icon=":material/block:",
                                    help="Enregistre la décision de ne retenir aucun levier."):
            if composants.executer(lambda: app.scenarios.retenir(utilisateur, dossier.id, None),
                                   "Décision enregistrée"):
                st.rerun()

    with droite:
        panneau_agent.afficher(app, utilisateur, dossier, modifiable)

    bouton_suite("acomptes", "Étape suivante : acomptes")
