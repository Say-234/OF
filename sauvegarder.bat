@echo off
rem Sauvegarde la base du cabinet. Passez un dossier en argument (ex. disque externe) : sauvegarder.bat E:\OptiFisc
rem À planifier chaque jour avec le Planificateur de tâches de Windows.
cd /d "%~dp0"
".venv\Scripts\python.exe" scripts\sauvegarder.py %1
