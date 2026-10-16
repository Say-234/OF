"""Outils partagés par les tests."""
from decimal import Decimal

from optifisc.domaine.balance import Balance, LigneBalance

M = 1_000_000  # un million de FCFA : rend les cas chiffrés lisibles


def balance(*lignes) -> Balance:
    """Construit une balance à partir de tuples (compte, libellé, débit, crédit) en entiers."""
    return Balance(tuple(LigneBalance(c, l, Decimal(d), Decimal(k)) for c, l, d, k in lignes))


def D(x) -> Decimal:
    """Raccourci : D(60 * M) ou D("0.30")."""
    return Decimal(x) if not isinstance(x, float) else Decimal(str(x))
