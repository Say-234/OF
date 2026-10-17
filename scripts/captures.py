"""Captures d'écran de l'application (pour le mémoire et la vérification visuelle).

Prérequis : l'application tourne en mode démo, par exemple :
    set OPTIFISC_MODE=demo & set OPTIFISC_MDP_DEMO=... & streamlit run src/optifisc/interface/streamlit/app.py
Puis :  python scripts/captures.py --url http://localhost:8501 --mot-de-passe ...
Utilise le Chrome installé sur le poste (Playwright, canal « chrome ») : aucun navigateur à télécharger.
"""
import argparse
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

SORTIE = Path(__file__).resolve().parents[1] / "var" / "captures"
ETAPES = ["Synthèse", "1 Balance", "2 Hypothèses", "3 Retraitements", "4 Calcul", "5 Leviers", "6 Acomptes",
          "7 Livrer"]


def attendre(page):
    """Attend la fin du calcul de la page (plus d'éléments « périmés » grisés pendant le rafraîchissement)."""
    page.wait_for_timeout(800)
    page.wait_for_function("() => !document.querySelector('[data-stale=\"true\"]')", timeout=30_000)
    page.wait_for_timeout(1200)


def capturer(page, nom: str):
    attendre(page)
    page.screenshot(path=str(SORTIE / f"{nom}.png"), full_page=True)
    print("capture :", nom)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8501")
    parser.add_argument("--email", default="salim@demo.bj")
    parser.add_argument("--mot-de-passe", required=True)
    args = parser.parse_args()
    SORTIE.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        navigateur = p.chromium.launch(channel="chrome", headless=True)
        page = navigateur.new_page(viewport={"width": 1440, "height": 900})
        try:
            parcourir(page, args)
        except Exception:
            page.screenshot(path=str(SORTIE / "echec.png"), full_page=True)
            raise
        finally:
            navigateur.close()


def parcourir(page, args):
    page.goto(args.url)
    page.get_by_role("button", name="Se connecter").first.wait_for(timeout=60_000)
    capturer(page, "00_accueil")
    page.get_by_role("button", name="Se connecter").first.click()
    page.get_by_label("E-mail").wait_for(timeout=30_000)
    capturer(page, "01_connexion")
    page.get_by_label("E-mail").fill(args.email)
    page.get_by_label("Mot de passe").fill(args.mot_de_passe)
    page.get_by_role("button", name="Se connecter").click()
    dialogue = page.get_by_role("dialog")                 # accueil du tutoriel : à la PREMIÈRE connexion seulement
    try:
        dialogue.wait_for(timeout=15_000)
        capturer(page, "01b_tutoriel")
        dialogue.get_by_role("button", name="Plus tard").click()
    except PlaywrightTimeout:
        print("accueil du tutoriel déjà vu : pas de capture")
    tableau = page.locator("[data-testid='stDataFrame']").first
    tableau.wait_for(timeout=30_000)
    capturer(page, "02_dossiers")
    tableau.click(position={"x": 14, "y": 89})          # case de sélection de la 2e ligne (dossier calculé)
    onglets = page.locator("[data-testid='stMain'] [data-testid='stButtonGroup']").first   # pas la barre latérale
    onglets.wait_for(timeout=30_000)
    for i, etape in enumerate(ETAPES, 3):
        onglets.get_by_text(etape, exact=False).first.click()
        capturer(page, f"{i:02d}_{etape.split()[-1].lower()}")
    for i, lien in enumerate(["Référentiel des règles", "Journal d'audit", "Assistant CGI", "Mes missions"], 11):
        page.get_by_role("link", name=lien).click()
        capturer(page, f"{i:02d}_{lien.split()[0].lower()}")


if __name__ == "__main__":
    main()
