"""Implémente le port GenerateurLivrables : produit les fichiers Excel et Word d'un dossier."""
import re

from optifisc.application.livrables import DonneesLivrables, Livrable

from .excel import dossier_de_calcul
from .word import lettre_dgi, note_de_pilotage

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


class GenerateurOffice:
    def generer(self, d: DonneesLivrables) -> list[Livrable]:
        client = re.sub(r"[^A-Za-z0-9]+", "_", d.dossier.raison_sociale).strip("_")
        suffixe = "_PROJET" if d.provisoire else ""
        base = f"{client}_IS{d.dossier.exercice}_{d.date_edition:%Y%m%d}{suffixe}"
        livrables = [Livrable(f"Note_pilotage_{base}.docx", note_de_pilotage(d), DOCX),
                     Livrable(f"Dossier_calcul_{base}.xlsx", dossier_de_calcul(d), XLSX)]
        lettre = lettre_dgi(d)
        if lettre:
            livrables.append(Livrable(f"Lettre_DGI_acomptes_{base}.docx", lettre, DOCX))
        return livrables
