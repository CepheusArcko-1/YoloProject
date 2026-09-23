"""Application de bureau : affiche l'interface Flask dans une fenêtre native."""
import os
import sys
import threading

from yolo_detection import paths

os.chdir(paths.ROOT)

# Pas de fenêtre console : on s'en détache (Python 3.13.0 en ouvre une même via pythonw)
# et les messages vont dans un fichier journal
if os.name == 'nt':
    import ctypes
    ctypes.windll.kernel32.FreeConsole()
    # Identifiant propre pour que la barre des tâches affiche l'icône de l'application et non celle de Python
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('YoloProject.Detection')
os.makedirs(paths.LOGS, exist_ok=True)
sys.stdout = sys.stderr = open(paths.APPLICATION_LOG, 'w', encoding='utf-8', buffering=1)

import webview


LOADING_HTML = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
:root { --bg: #f5f6f8; --text: #16181d; --muted: #6b7280; --track: #e3e6ea; --accent: #4f46e5; }
@media (prefers-color-scheme: dark) {
  :root { --bg: #0e1015; --text: #eceef2; --muted: #9aa1ad; --track: #2a2f3a; --accent: #818cf8; }
}
body { margin: 0; height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 18px; font-family: "Segoe UI", system-ui, sans-serif; background: var(--bg); color: var(--text); }
.logo { width: 64px; height: 64px; border-radius: 18px; display: grid; place-items: center;
  background: linear-gradient(135deg, #6366f1, #8b5cf6); box-shadow: 0 10px 30px rgba(99, 102, 241, .35);
  animation: pulse 1.6s ease-in-out infinite; }
h1 { margin: 0; font-size: 20px; font-weight: 700; }
p { margin: -10px 0 0; color: var(--muted); font-size: 13px; }
.bar { width: 220px; height: 4px; border-radius: 4px; background: var(--track); overflow: hidden; }
.bar i { display: block; width: 40%; height: 100%; border-radius: 4px; background: var(--accent);
  animation: slide 1.2s ease-in-out infinite; }
@keyframes slide { from { transform: translateX(-100%); } to { transform: translateX(250%); } }
@keyframes pulse { 50% { transform: scale(1.06); } }
</style></head><body>
<div class="logo"><svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.4"
  stroke-linecap="round"><path d="M4 9V5a1 1 0 0 1 1-1h4M15 4h4a1 1 0 0 1 1 1v4M20 15v4a1 1 0 0 1-1 1h-4M9 20H5a1 1 0 0 1-1-1v-4"/>
  <circle cx="12" cy="12" r="2.5" fill="#fff" stroke="none"/></svg></div>
<h1>YOLO Detection</h1>
<p>Chargement du modèle YOLO26…</p>
<div class="bar"><i></i></div>
</body></html>"""


def windows_dark_mode():
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r'Software\Microsoft\Windows\CurrentVersion\Themes\Personalize')
        return winreg.QueryValueEx(key, 'AppsUseLightTheme')[0] == 0
    except OSError:
        return False


def style_window(window):
    """Icône de l'application et barre de titre sombre si Windows est en mode sombre."""
    try:
        from System.Drawing import Icon
        window.native.Icon = Icon(paths.ICON)
        if windows_dark_mode():
            hwnd = window.native.Handle.ToInt64()
            dark = ctypes.c_int(1)  # DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            ctypes.windll.dwmapi.DwmSetWindowAttribute(ctypes.c_void_p(hwnd), 20, ctypes.byref(dark),
                                                       ctypes.sizeof(dark))
    except Exception as e:
        print(f"Style de fenêtre non appliqué : {e!r}")


def start_server(window):
    # Import lourd (torch, modèle) fait pendant que l'écran de chargement est affiché
    try:
        from werkzeug.serving import make_server
        from yolo_detection.server import app
        # Permet à la désinstallation de fermer la fenêtre (après avoir répondu à la page)
        app.config['QUIT_APP'] = lambda: threading.Timer(0.5, window.destroy).start()
        server = make_server('127.0.0.1', 0, app, threaded=True)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        window.load_url(f'http://127.0.0.1:{server.server_port}/')
    except Exception as e:
        print(f'Erreur au démarrage : {e!r}')
        window.load_html(f'<p style="font-family:Segoe UI">Erreur au démarrage : {e}</p>'
                         f'<p style="font-family:Segoe UI">Détails dans {paths.APPLICATION_LOG}</p>')
        raise


if __name__ == '__main__':
    window = webview.create_window('YOLO Detection', html=LOADING_HTML, width=1180, height=800,
                                   min_size=(760, 560),
                                   background_color='#0e1015' if windows_dark_mode() else '#f5f6f8')
    window.events.shown += lambda: style_window(window)
    webview.start(start_server, window)
