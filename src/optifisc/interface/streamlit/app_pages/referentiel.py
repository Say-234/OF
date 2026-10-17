"""E15 — Référentiel des règles (UC10) : consultation pour tous, validation sur un cas chiffré par l'expert.

Les règles ne sont PAS modifiables à l'écran (doc 02, §4) : on modifie le YAML, on lance les tests,
puis l'expert re-valide ici. Une règle modifiée dans le YAML perd automatiquement sa validation.
"""
import streamlit as st

from optifisc.application.autorisation import peut
from optifisc.interface.streamlit import composants, etat, formats

app = etat.application()
utilisateur = etat.utilisateur()
ref = app.referentiel
validees = app.validation.regles_validees()
TYPES = {"totalite": "Totalité des comptes", "plafond_ca": "Plafond sur CA", "plafond_ebe": "Plafond d'intérêts",
         "saisie": "Saisie", "plafond_saisie": "Saisie plafonnée"}

actions = composants.entete(f"Référentiel des règles — {ref.millesime}",
                            "Règles appliquées par le moteur, avec leur article. L'expert-comptable valide chaque "
                            "règle sur un cas chiffré.")
with actions:
    composants.badge(f"Validées : {len(validees)} / {len(ref.regles)}", "info")

statut = st.segmented_control("Statut", ["Toutes", "À valider", "Validées"], default="Toutes", required=True,
                              label_visibility="collapsed")
regles = [r for r in ref.regles if statut == "Toutes" or (r.id in validees) == (statut == "Validées")]
evenement = st.dataframe([{"Réf.": r.id.split("_")[0], "Règle": r.libelle, "Article": r.article.replace("CGI ", ""),
                           "Type": TYPES[r.type.value], "Statut": "✓ validée" if r.id in validees else "▲ à valider"}
                          for r in regles], hide_index=True, on_select="rerun", selection_mode="single-row",
                         key=f"tableau_regles_{statut}", alt="Règles de retraitement")

if evenement.selection.rows:
    regle = regles[evenement.selection.rows[0]]
    with composants.carte():
        st.markdown(f"**{regle.id} — {regle.libelle}** · {regle.article}")
        details = {"Type": TYPES[regle.type.value], "Sens": regle.sens.value.replace("reintegration", "réintégration"),
                   "Catégorie": next(c.libelle for c in ref.categories if c.id == regle.categorie)}
        if regle.comptes:
            details["Comptes"] = ", ".join(regle.comptes)
        if regle.taux_plafond is not None:
            details["Taux du plafond"] = formats.pourcentage(regle.taux_plafond)
        if regle.plafond_montant is not None:
            details["Plafond"] = formats.montant(regle.plafond_montant, True)
        if regle.coefficient is not None:
            details["Part retenue"] = formats.pourcentage(regle.coefficient)
        st.table(details, border="horizontal", width="content")
        if regle.explication:
            st.write(regle.explication)
        validation = validees.get(regle.id)
        if validation:
            quand = formats.jour(validation["quand"]) if validation.get("quand") else ""
            st.success(f"Validée par {validation['valide_par']} {quand} — cas : {validation.get('cas', '')}",
                       icon=":material/verified:")
        if peut(utilisateur, "valider_regle"):
            if validation and validation.get("quand"):
                if st.button("Remettre « à valider »", type="tertiary"):
                    if composants.executer(lambda: app.validation.remettre_a_valider(utilisateur, regle.id)):
                        st.rerun()
            elif not validation:
                cas = st.text_input("Cas chiffré vérifié", placeholder="ex. Dons 2,1 M ; CA 150 M ; plafond 0,15 M "
                                                                     "→ réintégration 1,95 M")
                commentaire = st.text_input("Commentaire (facultatif)")
                if st.button("Valider la règle", type="primary", icon=":material/verified:"):
                    if composants.executer(lambda: app.validation.valider_regle(utilisateur, regle.id, cas,
                                                                                commentaire), "Règle validée"):
                        st.rerun()

with st.expander("Périmètre de l'outil : ce qui est couvert, non couvert, hypothèses"):
    perimetre = ref.perimetre
    st.write(perimetre.get("objet", ""))
    for titre, cle in (("Couvert", "couvert"), ("Non couvert", "non_couvert")):
        st.markdown(f"**{titre}**")
        for element in perimetre.get(cle, []):
            st.markdown(f"- **{element['titre']}** : {element['detail']}")
    st.markdown("**Hypothèses**")
    for hypothese in perimetre.get("hypotheses", []):
        st.markdown(f"- {hypothese}")
composants.pied_de_page()
