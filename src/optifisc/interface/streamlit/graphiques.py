"""Graphiques de l'interface (Altair, rendu natif Streamlit). Règles suivies : skill « dataviz ».

- La forme d'abord : un ratio = jauge (st.progress), une comparaison où UN montant compte = emphase
  (vert pour l'élément appliqué, gris pour le contexte), un avant/après = une teinte en deux nuances.
- Couleurs validées par le script du skill (paire #0B7A55 / #4CC38A : séparation daltonisme ΔE 22).
- Jamais la couleur seule : chaque barre porte sa valeur écrite ; un tableau existe toujours à côté.
- Un seul axe par graphique ; grille discrète ; infobulle au survol.
Les montants sont convertis en nombres À L'AFFICHAGE seulement (le calcul reste en Decimal).
"""
from decimal import Decimal

import altair as alt

from . import formats

VERT = "#0B7A55"
VERT_CLAIR = "#4CC38A"
GRIS = "#B9C6C0"
TEXTE = "#10231C"
TEXTE_SECONDAIRE = "#4A5E56"


def _m(valeur: Decimal) -> float:
    return float(valeur) / 1_000_000


def _style(graphique: alt.Chart, hauteur: int) -> alt.Chart:
    return (graphique.properties(height=hauteur)
            .configure_view(stroke=None)
            .configure_axis(grid=False, domainColor=GRIS, tickColor=GRIS, labelColor=TEXTE_SECONDAIRE,
                            titleColor=TEXTE_SECONDAIRE, labelFontSize=12, titleFontSize=12)
            .configure_legend(labelColor=TEXTE_SECONDAIRE, titleColor=TEXTE_SECONDAIRE, orient="top"))


def emphase_impot(is_droit_commun: Decimal, minimum: Decimal, au_minimum: bool) -> alt.Chart:
    """IS de droit commun vs minimum de perception : le montant APPLIQUÉ en vert, l'autre en gris (emphase)."""
    donnees = [
        {"libelle": "IS de droit commun (art. 46)", "montant": _m(is_droit_commun),
         "texte": formats.montant(is_droit_commun, True), "applique": not au_minimum},
        {"libelle": "Minimum de perception (art. 47)", "montant": _m(minimum),
         "texte": formats.montant(minimum, True), "applique": au_minimum},
    ]
    for d in donnees:
        d["statut"] = "appliqué" if d["applique"] else "non appliqué"
    base = alt.Chart(alt.Data(values=donnees)).encode(
        y=alt.Y("libelle:N", title=None, sort=None, axis=alt.Axis(labelLimit=260)),
        tooltip=[alt.Tooltip("libelle:N", title="Impôt"), alt.Tooltip("texte:N", title="Montant"),
                 alt.Tooltip("statut:N", title="Régime")])
    plus_grand = max(d["montant"] for d in donnees) or 1
    barres = base.mark_bar(cornerRadiusEnd=4, height=22).encode(
        # 45 % de marge à droite : l'étiquette « … · appliqué » tient sans être coupée
        x=alt.X("montant:Q", title="Millions de FCFA", axis=alt.Axis(format=",.0f"),
                scale=alt.Scale(domain=[0, plus_grand * 1.45])),
        color=alt.Color("applique:N", scale=alt.Scale(domain=[True, False], range=[VERT, GRIS]), legend=None))
    valeurs = base.mark_text(align="left", dx=6, fontSize=12, color=TEXTE).encode(
        x="montant:Q", text=alt.Text("etiquette:N")).transform_calculate(
        etiquette="datum.texte + (datum.applique ? '  · appliqué' : '')")
    return _style(barres + valeurs, 150)


def passage_resultat(resultat_comptable: Decimal, reintegrations: Decimal, deductions: Decimal,
                     deficits: Decimal, resultat_fiscal: Decimal) -> alt.Chart:
    """Cascade du résultat comptable au résultat fiscal : totaux en vert, mouvements en vert clair."""
    etapes = [("Résultat comptable", resultat_comptable, "total"), ("+ Réintégrations", reintegrations, "hausse"),
              ("− Déductions", -deductions, "baisse"), ("− Déficits imputés", -deficits, "baisse"),
              ("Résultat fiscal", resultat_fiscal, "total")]
    donnees, cumul = [], Decimal(0)
    for libelle, montant, nature in etapes:
        if nature == "total":
            debut, fin, cumul = Decimal(0), montant, montant
        else:
            debut, fin = cumul, cumul + montant
            cumul = fin
        donnees.append({"etape": libelle, "debut": _m(debut), "fin": _m(fin), "nature": nature,
                        "texte": formats.montant(abs(montant), True) if montant else "0"})
    base = alt.Chart(alt.Data(values=donnees)).encode(
        x=alt.X("etape:N", title=None, sort=None, axis=alt.Axis(labelAngle=0, labelLimit=150)),
        tooltip=[alt.Tooltip("etape:N", title="Étape"), alt.Tooltip("texte:N", title="Montant")])
    barres = base.mark_bar(cornerRadius=4, size=46).encode(
        y=alt.Y("debut:Q", title="Millions de FCFA", axis=alt.Axis(format=",.0f")), y2="fin:Q",
        color=alt.Color("nature:N", scale=alt.Scale(domain=["total", "hausse", "baisse"],
                                                    range=[VERT, VERT_CLAIR, GRIS]), legend=None))
    valeurs = base.mark_text(dy=-8, fontSize=12, color=TEXTE).encode(
        y=alt.Y("haut:Q"), text="texte:N").transform_calculate(haut="max(datum.debut, datum.fin)")
    return _style(barres + valeurs, 260)


def acomptes(echeances, acompte_demande: Decimal | None) -> alt.Chart:
    """Acomptes : montant normal et, si une réduction est demandée, montant demandé (une teinte, deux nuances)."""
    donnees = []
    for e in echeances:
        donnees.append({"echeance": formats.jour(e.date), "serie": "Acompte normal", "montant": _m(e.montant_normal),
                        "texte": formats.montant(e.montant_normal)})
        if acompte_demande is not None and not e.payee:
            donnees.append({"echeance": formats.jour(e.date), "serie": "Acompte demandé",
                            "montant": _m(acompte_demande), "texte": formats.montant(acompte_demande)})
    series = ["Acompte normal"] + (["Acompte demandé"] if acompte_demande is not None else [])
    base = alt.Chart(alt.Data(values=donnees)).encode(
        x=alt.X("echeance:N", title=None, sort=None, axis=alt.Axis(labelAngle=0)),
        xOffset=alt.XOffset("serie:N", sort=series),
        tooltip=[alt.Tooltip("echeance:N", title="Échéance"), alt.Tooltip("serie:N", title="Série"),
                 alt.Tooltip("texte:N", title="FCFA")])
    barres = base.mark_bar(cornerRadiusEnd=4, size=26).encode(
        y=alt.Y("montant:Q", title="Millions de FCFA", axis=alt.Axis(format=",.1f")),
        color=alt.Color("serie:N", title=None, sort=series,
                        scale=alt.Scale(domain=["Acompte normal", "Acompte demandé"], range=[VERT, VERT_CLAIR])))
    valeurs = base.mark_text(dy=-8, fontSize=11, color=TEXTE).encode(y="montant:Q", text="texte:N")
    return _style(barres + valeurs, 240)
