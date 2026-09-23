"""Emplacements de tous les fichiers de l'application.

Tout ce que l'application crée reste dans le dossier du projet :
  runtime/        Python embarqué et composants (créé à l'installation)
  data/models/    modèles YOLO26 téléchargés
  data/logs/      journaux d'installation et d'exécution
  data/results/   analyses, une par dossier (conservées à la désinstallation)
  data/settings.json  réglages (modèle choisi)
"""
import os
import sys

# Dossier du projet : celui de l'exécutable une fois compilé, sinon le parent de ce paquet
if getattr(sys, 'frozen', False):
    ROOT = os.path.dirname(sys.executable)
else:
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PACKAGE = os.path.join(ROOT, 'yolo_detection')
ICON = os.path.join(PACKAGE, 'static', 'icon.ico')
REQUIREMENTS = os.path.join(ROOT, 'requirements.txt')
EXECUTABLE = os.path.join(ROOT, 'YOLO Detection.exe')

RUNTIME = os.path.join(ROOT, 'runtime')
RUNTIME_PYTHON = os.path.join(RUNTIME, 'python.exe')
RUNTIME_PYTHONW = os.path.join(RUNTIME, 'pythonw.exe')
INSTALLED_MARKER = os.path.join(RUNTIME, 'installed.txt')

# Ancien emplacement (environnement virtuel) : seulement pour le retirer
LEGACY_VENV = os.path.join(ROOT, '.venv')

DATA = os.path.join(ROOT, 'data')
MODELS = os.path.join(DATA, 'models')
LOGS = os.path.join(DATA, 'logs')
RESULTS = os.path.join(DATA, 'results')
SETTINGS = os.path.join(DATA, 'settings.json')

INSTALL_LOG = os.path.join(LOGS, 'installation.log')
APPLICATION_LOG = os.path.join(LOGS, 'application.log')
