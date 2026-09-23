"""Liste et supprime ce que l'application a installé, et uniquement ça.

N'utilise que la bibliothèque standard : il est aussi embarqué dans « YOLO Detection.exe ».

Supprimé : l'environnement Python (.venv), le modèle téléchargé (data/models), les journaux (data/logs),
le raccourci du Bureau (seulement s'il pointe vers ce dossier) et les caches Python générés.
Conservé : le code du projet, l'exécutable, les résultats d'analyse (data/results)
et tout ce qui est hors de ce dossier (Python, cache pip, réglages Ultralytics partagés).
"""
import os
import shutil
import subprocess
import time

SHORTCUT_NAME = 'YOLO Detection.lnk'


def _size(path):
    if os.path.isfile(path):
        return os.path.getsize(path)
    total = 0
    for folder, _, files in os.walk(path):
        for name in files:
            try:
                total += os.path.getsize(os.path.join(folder, name))
            except OSError:
                pass
    return total


def _desktop_shortcut():
    script = ("$s = New-Object -ComObject WScript.Shell;"
              f"$p = Join-Path ([Environment]::GetFolderPath('Desktop')) '{SHORTCUT_NAME}';"
              "if (Test-Path $p) { $p; $s.CreateShortcut($p).TargetPath }")
    try:
        out = subprocess.run(['powershell', '-NoProfile', '-Command', script], capture_output=True, text=True,
                             creationflags=subprocess.CREATE_NO_WINDOW, timeout=20).stdout.splitlines()
    except (OSError, subprocess.SubprocessError):
        return None, None
    return (out[0], out[1]) if len(out) >= 2 else (None, None)


def find_items(root):
    """Renvoie [(libellé, chemin, taille en octets)] des éléments installés présents."""
    root = os.path.abspath(root)
    items = []

    venv = os.path.join(root, '.venv')
    if os.path.exists(os.path.join(venv, 'pyvenv.cfg')):
        items.append(('Environnement Python et composants (.venv)', venv))

    models = os.path.join(root, 'data', 'models')
    if os.path.isdir(models):
        items.append(('Modèle YOLO26 téléchargé (data/models)', models))

    shortcut, target = _desktop_shortcut()
    if shortcut and target and os.path.abspath(target).lower().startswith(root.lower() + os.sep):
        items.append(('Raccourci « YOLO Detection » du Bureau', shortcut))

    logs = os.path.join(root, 'data', 'logs')
    if os.path.isdir(logs):
        items.append(('Journaux (data/logs)', logs))

    for folder in ('yolo_detection', 'tests'):
        cache = os.path.join(root, folder, '__pycache__')
        if os.path.isdir(cache):
            items.append((f'Cache Python ({folder}/__pycache__)', cache))

    return [(label, path, _size(path)) for label, path in items]


def remove(path, timeout=20):
    """Supprime un fichier ou un dossier, en réessayant tant que l'application se ferme."""
    deadline = time.time() + timeout
    while True:
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            elif os.path.exists(path):
                os.remove(path)
            return
        except OSError:
            if time.time() > deadline:
                raise
            time.sleep(0.5)


def format_size(size):
    for unit in ('octets', 'Ko', 'Mo', 'Go'):
        if size < 1024 or unit == 'Go':
            return f'{size:.0f} {unit}' if unit == 'octets' else f'{size:.1f} {unit}'.replace('.', ',')
        size /= 1024
