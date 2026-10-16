@echo off
rem Lance OptiFisc sur ce poste (accessible seulement depuis ce poste : http://localhost:8501).
rem Premier lancement : crée l'environnement Python et installe les dépendances (quelques minutes).
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Installation de l'environnement Python...
    py -m venv .venv || (echo Python introuvable : installez Python 3.12 ou plus recent depuis python.org & pause & exit /b 1)
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    ".venv\Scripts\python.exe" -m pip install -e .
)
if not exist ".env" copy ".env.exemple" ".env" >nul
".venv\Scripts\python.exe" -m streamlit run src\optifisc\interface\streamlit\app.py --server.address localhost --server.port 8501
pause
