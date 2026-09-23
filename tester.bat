@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
    echo Lancez d'abord installer.bat.
    pause
    exit /b 1
)
.venv\Scripts\python -m unittest discover -s tests -v
if errorlevel 1 (echo. & echo ECHEC des tests) else (echo. & echo Tous les tests sont OK)
pause
