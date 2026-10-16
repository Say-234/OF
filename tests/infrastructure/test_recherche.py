"""J11 — recherche d'articles BM25 : les questions étalons (V1) retrouvent le bon article dans les 5 premiers."""
import pytest

from conftest import RACINE_REFERENTIEL
from optifisc.infrastructure.corpus import chapitre, charger_corpus
from optifisc.infrastructure.recherche_bm25 import RechercheBm25

RECHERCHE = RechercheBm25(charger_corpus(RACINE_REFERENTIEL / "corpus"))

ETALONS = [  # questions étalons de la V1 (périmètre IS) + deux questions du MVP
    ("Quel est le taux normal de l'impôt sur les sociétés ?", "46"),
    ("Quelles sociétés sont soumises à l'impôt sur les sociétés ?", "3"),
    ("Qu'est-ce que le minimum de perception de l'impôt sur les sociétés ?", "47"),
    ("Les dépenses liées à la chasse sont-elles déductibles du bénéfice imposable ?", "33"),
    ("Une amende fiscale payée par l'entreprise est-elle déductible ?", "36"),
    ("Quelle est la limite de déduction des dons faits par une entreprise ?", "32"),
    ("Peut-on reporter un déficit sur les exercices suivants pour l'impôt sur les sociétés ?", "43"),
    ("Quand faut-il payer le premier acompte de l'impôt sur les sociétés ?", "51"),
    ("Quel est le plafond de déduction des cadeaux publicitaires ?", "32"),
    ("Peut-on demander la réduction des acomptes d'impôt sur les sociétés ?", "52"),
]


@pytest.mark.parametrize("question, attendu", ETALONS)
def test_question_etalon_dans_les_5_premiers(question, attendu):
    assert attendu in [t.article.numero for t in RECHERCHE.rechercher(question, 5)]


def test_article_cite_dans_la_question_remonte_en_tete():
    assert RECHERCHE.rechercher("Que dit l'article 41 ?", 3)[0].article.numero == "41"


def test_chapitre_lisible():
    assert chapitre("LIVRE 1 > CHAPITRE 1 IMPOT SUR LES SOCIÉTÉS (IS) > SECTION 2") == "IS"


def test_similarite_entre_justification_et_article():
    assert RECHERCHE.similarite("dons libéralités plafond chiffre d'affaires", "32") > 0.5
    assert RECHERCHE.similarite("dons", "9999") == 0
