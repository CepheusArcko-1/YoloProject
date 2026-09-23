"""Application de bureau : affiche l'interface Flask dans une fenêtre native."""
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())

# Pas de fenêtre console : on s'en détache (Python 3.13.0 en ouvre une même via pythonw)
# et les messages vont dans un fichier journal
if os.name == 'nt':
    import ctypes
    ctypes.windll.kernel32.FreeConsole()
sys.stdout = sys.stderr = open('application.log', 'w', encoding='utf-8', buffering=1)

import webview
from app import app

if __name__ == '__main__':
    webview.create_window('YOLO26 Object Detection', app, width=1000, height=800, min_size=(600, 500))
    webview.start()
