"""J11 — assistant CGI et agent de propositions, avec une FAUSSE IA qui suit un scénario écrit d'avance.

Aucun appel réel : on vérifie le pare-feu de données et les garde-fous vérifiés par le code.
"""
import json
from dataclasses import replace
from datetime import date, datetime
from decimal import Decimal

import pytest

from conftest import DEMO
from optifisc.application.agent.boucle import lire_action
from optifisc.application.agent.profil import construire_profil_pseudonymise
from optifisc.application.agent.service import masquer_nombres
from optifisc.application.assistant import lire_reponse, probleme_pare_feu
from optifisc.composition import construire
from optifisc.domaine.dossier import Ajustement, CategorieTaux, Hypotheses, Secteur
from optifisc.domaine.erreurs import AccesRefuse, IAIndisponible
from optifisc.domaine.moteur.acomptes import echeancier
from optifisc.domaine.utilisateur import Role

M = 1_000_000


class FausseIA:
    """Rejoue des réponses écrites d'avance et garde les messages reçus (pour vérifier ce qui a été envoyé)."""
    disponible = True
    nom = "fausse IA"
    confidentiel = False

    def __init__(self, reponses):
        self.reponses = list(reponses)
        self.recus = []

    def discuter(self, messages):
        self.recus.append(messages)
        if not self.reponses:
            raise IAIndisponible("plus de réponse")
        return self.reponses.pop(0)


class HorlogeFigee:
    def maintenant(self):
        return datetime(2026, 9, 23, 10, 0)

    def aujourd_hui(self):
        return date(2026, 9, 23)


def application(tmp_path, ia, demonstration=True):
    app = construire(tmp_path / "ia.sqlite", horloge=HorlogeFigee(), fournisseur=ia, mode="cabinet")
    admin = app.comptes.connecter("a@c.bj", app.comptes.creer_premier_administrateur("a@c.bj", "A"))
    salim = app.comptes.connecter("s@c.bj", app.comptes.creer_utilisateur(admin, "s@c.bj", "Salim", Role.COLLABORATEUR))
    d = app.dossiers.creer(salim, "NOVA SERVICES SA", Secteur.AUTRES, CategorieTaux.DROIT_COMMUN, 2026, demonstration)
    contenu = (DEMO / "balance_NOVASERVICES_30-06-2026.xlsx").read_bytes()
    app.balance.confirmer(salim, d.id, app.balance.apercu(salim, d.id, contenu, "n.xlsx", date(2026, 6, 30)))
    app.dossiers.definir_hypotheses(salim, d.id, Hypotheses(mois_arrete=6, is_n_moins_1=Decimal(30 * M),
                                                            ajustements=(Ajustement("6813", "dot", Decimal(20 * M)),)))
    return app, salim, d.id


def action(outil, **arguments):
    return json.dumps({"outil": outil, "arguments": arguments})


# ------------------------------------------------------------------ assistant et pare-feu
def test_pare_feu_bloque_montants_et_noms_de_clients():
    assert probleme_pare_feu("Le client a payé 1 500 000 FCFA d'amendes", [])
    assert probleme_pare_feu("NOVA SERVICES peut-elle déduire ses dons ?", ["NOVA SERVICES"])
    assert probleme_pare_feu("Quel est le plafond des dons (article 32) en 2026 ?", ["NOVA SERVICES"]) == ""


def test_lecture_de_la_reponse_structuree():
    reponse, articles = lire_reponse("Réponse : 3 ‰ du CA HT.\nArticle(s) : 32, 32-3")
    assert reponse == "3 ‰ du CA HT." and articles == ["32", "32-3"]


def test_assistant_n_envoie_que_la_question_et_les_articles(tmp_path):
    ia = FausseIA(["Réponse : dans la limite de 1 ‰ du CA HT.\nArticle(s) : 32"])
    app, salim, _ = application(tmp_path, ia)
    r = app.assistant.poser(salim, "Quelle est la limite de déduction des dons ?")
    assert r.sourcee and r.articles_cites == ("32",)
    envoye = json.dumps(ia.recus[0], ensure_ascii=False)
    assert "NOVA" not in envoye                                   # aucune donnée du dossier dans l'appel


def test_assistant_bloque_une_question_avec_un_nom_de_client(tmp_path):
    ia = FausseIA([])
    app, salim, _ = application(tmp_path, ia)
    r = app.assistant.poser(salim, "NOVA SERVICES SA peut-elle déduire ses dons ?")
    assert "non envoyée" in r.message and ia.recus == [] and r.articles   # articles locaux quand même


# ------------------------------------------------------------------ agent
def scenario_agent():
    return [
        action("lire_profil"),
        action("lister_leviers"),
        action("simuler_levier", id_levier="L03_PROVISION_JUSTIFIEE",
               parametres={"montant": "10000000", "justifiee": True, "au_releve": True}),
        action("proposer", type="levier", titre="Provisionner le litige client", article="41",
               justification="Provision pour perte probable, nettement précisée, de 10 000 000 FCFA.",
               id_levier="L03_PROVISION_JUSTIFIEE",
               parametres={"montant": "10000000", "justifiee": True, "au_releve": True}),
        action("proposer", type="piste", titre="Plus-value réinvestie", article="17",
               justification="Exonération de la plus-value de cession avec engagement de réinvestir."),
        action("proposer", type="piste", titre="Article inventé", article="999", justification="Inventé."),
        "texte sans JSON",
        json.dumps({"fin": True}),
    ]


def test_agent_garde_fous_verifies_par_le_code(tmp_path):
    ia = FausseIA(scenario_agent())
    app, salim, dossier_id = application(tmp_path, ia)
    r = app.agent.demander(salim, dossier_id)
    titres = {p.titre: p for p in r.propositions}
    assert set(titres) == {"Provisionner le litige client", "Plus-value réinvestie"}
    assert any("Article inventé" in rej for rej in r.rejetees)               # article 999 rejeté
    levier = titres["Provisionner le litige client"]
    assert levier.gain == 3 * M                                              # 10 M × 30 % : calculé par le moteur
    assert "10 000 000" not in levier.justification                          # nombre de l'IA masqué
    assert titres["Plus-value réinvestie"].gain is None                      # une piste n'est jamais chiffrée
    assert r.arret == "terminé par l'agent"
    tout_ce_qui_a_ete_envoye = json.dumps(ia.recus, ensure_ascii=False)
    assert "NOVA" not in tout_ce_qui_a_ete_envoye                            # pare-feu : jamais la raison sociale


def test_levier_accepte_devient_un_scenario_et_piste_ecartee_avec_motif(tmp_path):
    app, salim, dossier_id = application(tmp_path, FausseIA(scenario_agent()))
    app.calcul.calculer(salim, dossier_id)
    r = app.agent.demander(salim, dossier_id)
    levier = next(p for p in r.propositions if p.type == "levier")
    piste = next(p for p in r.propositions if p.type == "piste")
    app.agent.decider(salim, dossier_id, levier.id, accepter=True)
    assert len(app.scenarios.lister(salim, dossier_id)) == 1
    with pytest.raises(Exception, match="motif"):
        app.agent.decider(salim, dossier_id, piste.id, accepter=False)
    app.agent.decider(salim, dossier_id, piste.id, accepter=False, motif="non applicable : pas de cession prévue")
    decisions = {p.id: p.decision for p in app.agent.lister(salim, dossier_id)[0]}
    assert decisions == {levier.id: "acceptee", piste.id: "ecartee"}


def test_dossier_reel_refuse_avec_un_fournisseur_en_ligne(tmp_path):
    app, salim, dossier_id = application(tmp_path, FausseIA(scenario_agent()), demonstration=False)
    with pytest.raises(AccesRefuse, match="Dossier réel"):
        app.agent.demander(salim, dossier_id)


def test_profil_pseudonymise_sans_donnee_identifiante(tmp_path):
    app, salim, dossier_id = application(tmp_path, FausseIA([]))
    dossier = app.dossiers.ouvrir(salim, dossier_id)
    resultat = app.calcul.resultat(salim, dossier_id)
    profil = construire_profil_pseudonymise(replace(dossier, raison_sociale="SECRET SARL"), resultat,
                                            echeancier(dossier, resultat, app.referentiel, date(2026, 9, 23)),
                                            app.referentiel)
    texte = profil.en_texte()
    assert "SECRET" not in texte and "NOVA" not in texte
    assert "chiffre_affaires_millions : 800" in texte                       # agrégats arrondis au million


def test_ia_indisponible_n_arrete_pas_l_agent(tmp_path):
    app, salim, dossier_id = application(tmp_path, FausseIA([]))
    r = app.agent.demander(salim, dossier_id)
    assert r.propositions == () and "plus de réponse" in r.arret


def test_outils_utilitaires():
    assert lire_action('Voici : {"outil": "lire_profil", "arguments": {}} merci') == {"outil": "lire_profil",
                                                                                     "arguments": {}}
    assert lire_action("pas de json") is None
    assert masquer_nombres("gain de 3 000 000 FCFA selon l'art. 41") == "gain de [montant masqué] FCFA selon l'art. 41"
