"""Outils partagés par les tests."""
from decimal import Decimal
from pathlib import Path

from optifisc.domaine.balance import Balance, LigneBalance
from optifisc.domaine.dossier import Ajustement, CategorieTaux, Dossier, Hypotheses, Secteur
from optifisc.infrastructure.referentiel_yaml import ReferentielYaml

M = 1_000_000  # un million de FCFA : rend les cas chiffrés lisibles
RACINE_REFERENTIEL = Path(__file__).resolve().parents[1] / "referentiel"
DEMO = RACINE_REFERENTIEL / "demo"


# Le vrai référentiel 2026 : les tests chiffrés portent sur les règles réellement utilisées.
REF = ReferentielYaml(RACINE_REFERENTIEL).charger(2026)


def dossier(secteur="autres", categorie_taux="droit_commun", saisies=None, ajustements=(), **hypotheses) -> Dossier:
    """Dossier de test : exercice complet (mois 12) sauf indication contraire. Montants en entiers."""
    valeurs = {"mois_arrete": 12}
    valeurs.update(hypotheses)
    for nom in ("is_n_moins_1", "aib_imputable", "deficits_anterieurs", "acomptes_payes"):
        if valeurs.get(nom) is not None:
            valeurs[nom] = Decimal(valeurs[nom])
    ajust = tuple(Ajustement(c, "ajustement", Decimal(m)) for c, m in ajustements)
    return Dossier(id="test", raison_sociale="Test", secteur=Secteur(secteur),
                   categorie_taux=CategorieTaux(categorie_taux), hypotheses=Hypotheses(ajustements=ajust, **valeurs),
                   saisies={k: Decimal(v) for k, v in (saisies or {}).items()})


def balance(*lignes) -> Balance:
    """Construit une balance à partir de tuples (compte, libellé, débit, crédit) en entiers."""
    return Balance(tuple(LigneBalance(c, lib, Decimal(d), Decimal(k)) for c, lib, d, k in lignes))


def D(x) -> Decimal:
    """Raccourci : D(60 * M) ou D("0.30")."""
    return Decimal(x) if not isinstance(x, float) else Decimal(str(x))
