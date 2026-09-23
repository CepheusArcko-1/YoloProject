"""Emplacements de tous les fichiers de l'application.

Tout ce que l'application crée reste dans le dossier du projet :
  .venv/          environnement Python et composants (créé à l'installation)
  data/models/    modèle YOLO26 téléchargé
  data/logs/      journaux d'installation et d'exécution
  data/results/   résultats des analyses (conservés à la désinstallation)
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

VENV = os.path.join(ROOT, '.venv')
VENV_PYTHON = os.path.join(VENV, 'Scripts', 'python.exe')
VENV_PYTHONW = os.path.join(VENV, 'Scripts', 'pythonw.exe')
INSTALLED_MARKER = os.path.join(VENV, 'installed.txt')

DATA = os.path.join(ROOT, 'data')
MODELS = os.path.join(DATA, 'models')
LOGS = os.path.join(DATA, 'logs')
RESULTS = os.path.join(DATA, 'results')

MODEL = os.path.join(MODELS, 'yolo26n.pt')
INSTALL_LOG = os.path.join(LOGS, 'installation.log')
APPLICATION_LOG = os.path.join(LOGS, 'application.log')
