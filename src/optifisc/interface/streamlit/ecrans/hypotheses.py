"""E07 — Hypothèses de projection (UC06) : ce que SUPPOSE le collaborateur, distinct de ce que dit la balance."""
from decimal import Decimal

import streamlit as st

from optifisc.domaine.dossier import Ajustement, Hypotheses
from optifisc.domaine.moteur.projection import facteur_projection
from optifisc.interface.streamlit import composants, formats

from . import bandeau_fige, bouton_suite, peut_modifier


def afficher(app, utilisateur, dossier, derniere_balance):
    composants.entete("Hypothèses de projection",
                      "Projeter la balance au 31/12 et renseigner ce que la balance ne contient pas.")
    bandeau_fige(dossier)
    h = dossier.hypotheses
    modifiable = peut_modifier(utilisateur, dossier)
    st.caption(f"Balance arrêtée à fin {formats.MOIS[h.mois_arrete - 1]} : projection = réalisé × "
               f"{facteur_projection(h):.2f} (même rythme d'activité). Seuls les comptes de gestion sont projetés.")

    with st.form(f"hypotheses_{dossier.id}", border=True):
        st.markdown("**Projection**")
        coef = st.number_input("Rythme d'activité du reste de l'année", min_value=0.0, max_value=3.0, step=0.05,
                               value=float(h.coef_activite), disabled=not modifiable,
                               help="1 = le reste de l'année ressemble au passé ; 0,8 = activité 20 % plus faible.")
        st.markdown("**Ajustements de fin d'année** — dotations non encore passées, charges connues "
                    "(montant positif = charge)")
        lignes = [{"Compte": a.compte, "Libellé": a.libelle, "Montant (FCFA)": formats.montant(a.montant)}
                  for a in h.ajustements] or [{"Compte": "6813", "Libellé": "Dotations aux amortissements à passer",
                                               "Montant (FCFA)": ""}]
        ajustements = st.data_editor(lignes, num_rows="dynamic" if modifiable else "fixed", disabled=not modifiable,
                                     hide_index=True, key=f"ajustements_{dossier.id}",
                                     column_config={"Montant (FCFA)": st.column_config.TextColumn(alignment="right")})
        st.markdown("**Informations hors balance**")
        colonnes = st.columns(3)
        with colonnes[0]:
            is_n1, ok1 = composants.champ_montant(f"IS dû au titre de {dossier.exercice - 1}", f"is_n1_{dossier.id}",
                                                  h.is_n_moins_1, "Base des acomptes (art. 51)", not modifiable)
        with colonnes[1]:
            aib, ok2 = composants.champ_montant("AIB supporté et imputable", f"aib_{dossier.id}", h.aib_imputable,
                                                "Art. 133-4", not modifiable)
        with colonnes[2]:
            deficits, ok3 = composants.champ_montant("Déficits antérieurs reportables", f"def_{dossier.id}",
                                                     h.deficits_anterieurs, "Art. 43 (5 exercices)", not modifiable)
        envoye = st.form_submit_button("Enregistrer les hypothèses", type="primary", disabled=not modifiable)

    if envoye:
        erreurs = []
        retenus = []
        for i, ligne in enumerate(ajustements, 1):
            compte = str(ligne.get("Compte") or "").strip()
            texte = str(ligne.get("Montant (FCFA)") or "").strip()
            if not compte and not texte:
                continue
            try:
                montant = formats.lire_montant(texte)
            except ValueError as exc:
                erreurs.append(f"ajustement {i} : {exc}")
                continue
            if not compte.isdigit() or montant is None:
                erreurs.append(f"ajustement {i} : compte numérique et montant obligatoires")
                continue
            retenus.append(Ajustement(compte, str(ligne.get("Libellé") or "Ajustement"), montant))
        if erreurs or not (ok1 and ok2 and ok3):
            st.error("Corrigez les saisies : " + " ; ".join(erreurs or ["montant illisible"]), icon=":material/error:")
        else:
            nouvelles = Hypotheses(mois_arrete=h.mois_arrete, coef_activite=Decimal(str(round(coef, 2))),
                                   ajustements=tuple(retenus), is_n_moins_1=is_n1 or Decimal(0),
                                   aib_imputable=aib or Decimal(0), deficits_anterieurs=deficits or Decimal(0),
                                   acomptes_payes=h.acomptes_payes)
            if composants.executer(lambda: app.dossiers.definir_hypotheses(utilisateur, dossier.id, nouvelles),
                                   "Hypothèses enregistrées"):
                st.rerun()

    if app.dependances.donnees.lire(dossier.id, "hypotheses_confirmees"):
        bouton_suite("retraitements", "Étape suivante : retraitements")
