"""Prépare les fichiers du logo à partir des images fournies par Salim (docs/identite/).

Les originaux sont des JPG sur un grand fond blanc. Ce script, sans rien redessiner :
  1. recadre au plus près du dessin ;
  2. rend le fond transparent (l'opacité suit l'intensité du trait, les bords restent lisses) ;
  3. ramène chaque pixel à la couleur exacte de la charte : vert #0E6B4E ou presque-noir #10231C ;
  4. produit trois versions dans interface/streamlit/static/ :
       logo_complet.png  monogramme au-dessus du nom (page d'accueil, connexion)
       logo.png          monogramme à gauche du nom, sur une ligne (barre latérale)
       icone.png         monogramme seul, carré (barre repliée, onglet du navigateur)

Lancer depuis OF/ :  python scripts/preparer_logo.py
"""
from pathlib import Path

from PIL import Image

RACINE = Path(__file__).resolve().parents[1]
SOURCES = RACINE / "docs" / "identite"
STATIQUE = RACINE / "src" / "optifisc" / "interface" / "streamlit" / "static"
VERT = (0x0E, 0x6B, 0x4E)
NOIR = (0x10, 0x23, 0x1C)
SEUIL_BRUIT = 40              # gris très pâles laissés par la compression JPG : effacés
CLARTE_DU_TRAIT = 90          # luminance du trait plein (le vert vaut environ 76) : au-delà, le pixel s'estompe


def detourer(image: Image.Image) -> Image.Image:
    """Fond blanc → transparent ; couleur ramenée à la charte (vert si le pixel est verdâtre, sinon presque-noir)."""
    rgb = image.convert("RGB")
    sortie = Image.new("RGBA", rgb.size)
    pixels = []
    for r, g, b in rgb.get_flattened_data():
        opacite = round((255 - (0.3 * r + 0.59 * g + 0.11 * b)) * 255 / (255 - CLARTE_DU_TRAIT))
        opacite = 0 if opacite < SEUIL_BRUIT else min(255, opacite)
        pixels.append((*(VERT if g - r > 25 else NOIR), opacite))
    sortie.putdata(pixels)
    return sortie


def recadrer(image: Image.Image, marge: int = 0) -> Image.Image:
    alpha = image.getchannel("A").point(lambda a: 255 if a > 40 else 0)
    gauche, haut, droite, bas = alpha.getbbox()
    return image.crop((gauche - marge, haut - marge, droite + marge, bas + marge))


def hauteur(image: Image.Image, h: int) -> Image.Image:
    return image.resize((round(image.width * h / image.height), h), Image.Resampling.LANCZOS)


def main() -> None:
    complet = recadrer(detourer(Image.open(SOURCES / "logo_source_complet.jpg")), 8)
    monogramme = recadrer(detourer(Image.open(SOURCES / "logo_source_monogramme.jpg")), 4)
    # le nom « OptiFisc » est la moitié basse du logo complet (sous le monogramme)
    bas = complet.crop((0, round(complet.height * 0.52), complet.width, complet.height))
    nom = recadrer(bas, 2)

    hauteur(complet, 360).save(STATIQUE / "logo_complet.png", optimize=True)

    # version sur une ligne : monogramme un peu plus haut que le nom, espace d'un quart de monogramme
    h_nom = 120
    nom_r = hauteur(nom, h_nom)
    mono_r = hauteur(monogramme, round(h_nom * 1.45))
    espace = mono_r.width // 4
    ligne = Image.new("RGBA", (mono_r.width + espace + nom_r.width, mono_r.height), (0, 0, 0, 0))
    ligne.paste(mono_r, (0, 0), mono_r)
    ligne.paste(nom_r, (mono_r.width + espace, (mono_r.height - nom_r.height) // 2 + 6), nom_r)
    ligne.save(STATIQUE / "logo.png", optimize=True)

    # icône carrée : monogramme centré
    cote = max(monogramme.size)
    carre = Image.new("RGBA", (cote, cote), (0, 0, 0, 0))
    carre.paste(monogramme, ((cote - monogramme.width) // 2, (cote - monogramme.height) // 2), monogramme)
    carre.resize((256, 256), Image.Resampling.LANCZOS).save(STATIQUE / "icone.png", optimize=True)
    for f in ("logo_complet.png", "logo.png", "icone.png"):
        print(f, Image.open(STATIQUE / f).size)


if __name__ == "__main__":
    main()
