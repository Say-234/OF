"""E14 — Assistant CGI (UC09) : articles trouvés localement (tout de suite), puis proposition de réponse de l'IA."""
import streamlit as st

from optifisc.interface.streamlit import composants, etat

app = etat.application()
utilisateur = etat.utilisateur()
ia = app.assistant.fournisseur

composants.entete("Assistant CGI", "Retrouver et comprendre un article du CGI 2026 ou du LPF 2024.")
if ia.disponible:
    st.caption(f":material/info: Ne saisissez ni nom de client ni montant : la question est envoyée à un service "
               f"d'IA en ligne ({ia.nom}).")
else:
    st.caption(":material/info: IA désactivée sur ce poste : la recherche d'articles reste disponible.")

with st.form("question", border=False):
    with st.container(horizontal=True, vertical_alignment="bottom"):
        question = st.text_input("Question", placeholder="Quel est le plafond de déduction des cadeaux publicitaires ?",
                                 label_visibility="collapsed")
        envoye = st.form_submit_button("Chercher", type="primary", icon=":material/search:")

if envoye and question.strip():
    articles, reponse = st.columns([2, 1], gap="large")
    trouves = composants.executer(lambda: app.assistant.poser(utilisateur, question, avec_ia=False))
    with articles:
        st.subheader("Articles trouvés", anchor=False)
        if trouves is None or not trouves.articles:
            composants.vide("Aucun article ne correspond : reformulez avec les mots du CGI.")
        for t in (trouves.articles if trouves else ()):
            pleins = max(1, round(t.pertinence * 5))
            with st.expander(f"{t.article.source} art. {t.article.numero} · {t.article.chapitre or '—'} · "
                             f"{'■' * pleins}{'□' * (5 - pleins)}"):
                st.write(t.article.texte)
    with reponse:
        with st.container(border=True):
            st.markdown("**Proposition de réponse**")
            if not ia.disponible:
                st.caption("IA désactivée.")
            else:
                with st.spinner("Rédaction par l'IA…"):
                    resultat = composants.executer(lambda: app.assistant.poser(utilisateur, question))
                if resultat and resultat.reponse:
                    st.caption("Générée par IA, à vérifier dans les articles cités.")
                    st.write(resultat.reponse)
                    st.markdown(f"Article(s) : {', '.join(resultat.articles_cites) or 'aucun'}")
                    if not resultat.sourcee:
                        composants.badge("Réponse non sourcée dans les articles fournis", "a_faire")
                    st.caption(resultat.modele)
                elif resultat:
                    st.info(resultat.message, icon=":material/info:")
composants.pied_de_page()
