"""E00 — Accueil (révision du 17/10/2026, remplace la décision D4.4) : ce qu'est OptiFisc, qui fait quoi, et
comment l'application accompagne l'année fiscale, du 30 juin au 31 décembre. Visible avant la connexion
(démo et cabinet) et, une fois connecté, depuis le menu « Découvrir OptiFisc ».
"""
import streamlit as st

from optifisc.interface.streamlit import composants, etat

app = etat.application()
utilisateur = etat.utilisateur()


def bouton_principal(cle: str) -> None:
    if utilisateur is None:
        if st.button("Se connecter", type="primary", icon=":material/login:", key=f"{cle}_connexion"):
            st.switch_page("app_pages/connexion.py")
    elif st.button("Voir mes missions", type="primary", icon=":material/flag:", key=f"{cle}_missions"):
        st.switch_page("app_pages/missions.py")


# ------------------------------------------------------------------ bandeau d'ouverture
with composants.carte():
    st.space("small")
    st.badge("CGI Bénin 2026 · impôt sur les sociétés", color="green", icon=":material/account_balance:")
    st.title("Piloter l'IS pendant l'exercice, pas après.", anchor=False)
    st.markdown("OptiFisc aide un cabinet d'expertise comptable à **estimer l'impôt sur les sociétés dès la "
                "balance du 30 juin**, à repérer les leviers d'optimisation **légaux**, à ajuster les acomptes et à "
                "livrer au client une note claire, validée par l'expert-comptable.")
    with st.container(horizontal=True):
        bouton_principal("haut")
        if app.mode == "demo":
            st.badge("Instance de démonstration · données fictives", color="orange", icon=":material/science:")
    st.space("small")

# ------------------------------------------------------------------ à quoi ça sert
st.subheader("Ce que vous y gagnez", anchor=False)
for colonne, (icone, titre, texte) in zip(st.columns(3), (
        ("trending_up", "Anticiper", "Un IS prévisionnel sur l'année entière, six mois avant la clôture : "
         "plus de mauvaise surprise au moment de la déclaration."),
        ("balance", "Optimiser légalement", "Chaque levier est rattaché à un article du CGI ; le moteur chiffre "
         "son effet, l'expert décide."),
        ("savings", "Préserver la trésorerie", "Si l'impôt baisse, OptiFisc calcule la réduction d'acompte "
         "à demander au DGI, et la date limite."),
), strict=True):
    with colonne, composants.carte():
        st.markdown(f"#### :primary[:material/{icone}:] {titre}")
        st.caption(texte)

# ------------------------------------------------------------------ l'année fiscale
st.subheader("Une année avec OptiFisc", anchor=False)
st.caption("Exercice civil : du 1er janvier au 31 décembre. OptiFisc intervient à partir de la balance semestrielle.")
ETAPES_ANNEE = (
    ("30/06", "Balance semestrielle", "Le collaborateur importe la balance ; OptiFisc la contrôle et projette "
     "l'année.", "upload_file"),
    ("Juillet", "Calcul et leviers", "IS prévisionnel, passage du résultat comptable au fiscal, scénarios "
     "d'optimisation.", "calculate"),
    ("Avant le 10/08 et le 10/11", "Acomptes", "Demande de réduction au DGI, 30 jours avant les acomptes du "
     "10/09 et du 10/12 (art. 52).", "mail"),
    ("31/12", "Clôture", "Les décisions prises (investissements, dotations) sont dans les comptes. Dossier validé "
     "et livré.", "event_available"),
    ("30/04 N+1", "Déclaration", "La déclaration se prépare sur une base déjà connue et documentée (art. 49).",
     "task_alt"),
)
for colonne, (quand, titre, texte, icone) in zip(st.columns(len(ETAPES_ANNEE)), ETAPES_ANNEE, strict=True):
    with colonne, composants.carte():
        st.badge(quand, color="green", icon=f":material/{icone}:")
        st.markdown(f"**{titre}**")
        st.caption(texte)

# ------------------------------------------------------------------ qui fait quoi
st.subheader("Qui fait quoi", anchor=False)
ROLES = (
    ("badge", "Collaborateur", "Prépare et analyse", ["Importe la balance et confirme les hypothèses",
     "Complète les retraitements et lance le calcul", "Étudie les leviers, décide des acomptes",
     "Soumet le dossier à l'expert"]),
    ("verified_user", "Expert-comptable", "Valide et engage le cabinet", ["Relit la synthèse et les points "
     "d'attention", "Valide les règles du référentiel", "Valide ou renvoie le dossier avec un motif",
     "Génère les livrables définitifs"]),
    ("admin_panel_settings", "Administrateur", "Organise et trace", ["Crée les comptes et attribue les dossiers",
     "Désactive un compte en cas de départ", "Consulte le journal d'audit",
     "Consulte les dossiers, sans les modifier"]),
)
for colonne, (icone, role, mission, taches) in zip(st.columns(3), ROLES, strict=True):
    with colonne, composants.carte():
        st.markdown(f"#### :primary[:material/{icone}:] {role}")
        st.caption(mission)
        st.markdown("\n".join(f"- {t}" for t in taches))

# ------------------------------------------------------------------ comment ça marche + garanties
gauche, droite = st.columns([3, 2])
with gauche, composants.carte():
    st.markdown("#### :primary[:material/route:] Le parcours d'un dossier")
    for numero, (phase, detail) in enumerate((
            ("Préparer", "balance, hypothèses, retraitements"), ("Analyser", "calcul de l'IS, leviers, agent IA"),
            ("Décider", "acomptes, soumission, validation par l'expert"), ("Livrer", "note Word et classeur Excel")),
            1):
        st.markdown(f"**{numero}. {phase}** · :gray[{detail}]")
    st.caption("Après la connexion, votre **journal de missions** vous guide pas à pas dans ce parcours, "
               "selon votre rôle. Vous pouvez le revoir à tout moment.")
with droite, composants.carte():
    st.markdown("#### :primary[:material/shield:] Nos garanties")
    composants.liste_de_points([
        ("fait", "L'IA propose, le moteur chiffre, l'humain décide."),
        ("fait", "Les montants viennent d'un moteur de règles testé, jamais de l'IA."),
        ("fait", "Aucune donnée client identifiable n'est envoyée à l'IA."),
        ("fait", "Chaque action est tracée dans un journal non modifiable."),
    ])

with st.container(horizontal=True, horizontal_alignment="center"):
    bouton_principal("bas")
composants.pied_de_page()
