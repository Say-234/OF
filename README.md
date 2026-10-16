# OptiFisc

Pilotage de l'**impôt sur les sociétés** en cours d'exercice pour les cabinets d'expertise comptable
au Bénin (CGI 2026). Prototype du mémoire DECOFI.

> L'IA ne calcule jamais un impôt : tout montant sort d'un moteur de règles déterministe, testé, et
> relié à un article du CGI. L'IA retrouve et explique les textes, et propose des pistes ; le moteur
> chiffre ; l'humain décide.

- Conception : [`docs/`](docs/README.md) (commencer par `docs/README.md`)
- Consignes pour les agents IA : [`AGENTS.md`](AGENTS.md)
- Suivi du travail : [`docs/JOURNAL_DE_BORD.md`](docs/JOURNAL_DE_BORD.md)

## Installation (Windows)

Prérequis : Python 3.12 ou plus récent ([python.org](https://www.python.org/downloads/), cocher « Add to PATH »).
Double-cliquer sur **`lancer.bat`** : il installe tout au premier lancement puis ouvre l'application.
Mise en service détaillée (cabinet, IA, démonstration en ligne, sauvegardes) : [`docs/08_mise_en_service.md`](docs/08_mise_en_service.md).

Pour développer :

```bat
py -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
copy .env.exemple .env
```

## Commandes

```bat
.venv\Scripts\python -m pytest -q          :: lancer les tests
.venv\Scripts\python -m ruff check .       :: vérifier le style
lancer.bat                                  :: lancer l'application (http://localhost:8501)
sauvegarder.bat E:\OptiFisc                  :: sauvegarder la base du cabinet
```
