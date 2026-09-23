"""Application de bureau : affiche l'interface Flask dans une fenêtre native."""
import os
import sys
import threading

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())

# Pas de fenêtre console : on s'en détache (Python 3.13.0 en ouvre une même via pythonw)
# et les messages vont dans un fichier journal
if os.name == 'nt':
    import ctypes
    ctypes.windll.kernel32.FreeConsole()
sys.stdout = sys.stderr = open('application.log', 'w', encoding='utf-8', buffering=1)

import webview

LOADING_HTML = """<!DOCTYPE html><html><body style="margin:0;height:100vh;display:flex;flex-direction:column;
align-items:center;justify-content:center;font-family:'Segoe UI',sans-serif;background:#f4f5f7;color:#1f2328">
<div style="width:56px;height:56px;border:6px solid #e6e8eb;border-top-color:#0969da;border-radius:50%;
animation:spin 0.9s linear infinite"></div>
<p style="margin-top:18px">Chargement du modèle YOLO26…</p>
<style>@keyframes spin{to{transform:rotate(360deg)}}</style></body></html>"""


def start_server(window):
    # Import lourd (torch, modèle) fait pendant que l'écran de chargement est affiché
    try:
        from werkzeug.serving import make_server
        from app import app
        server = make_server('127.0.0.1', 0, app, threaded=True)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        window.load_url(f'http://127.0.0.1:{server.server_port}/')
    except Exception as e:
        print(f'Erreur au démarrage : {e!r}')
        window.load_html(f'<p style="font-family:Segoe UI">Erreur au démarrage : {e}</p>'
                         '<p style="font-family:Segoe UI">Détails dans application.log</p>')
        raise


if __name__ == '__main__':
    window = webview.create_window('YOLO26 Object Detection', html=LOADING_HTML,
                                   width=1000, height=800, min_size=(600, 500))
    webview.start(start_server, window)
