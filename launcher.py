"""Lanceur de YOLO Detection : installe l'application au premier lancement, puis l'ouvre.

Compilé en « YOLO Detection.exe » (voir README). N'utilise que la bibliothèque standard.
"""
import hashlib
import os
import queue
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox

FROZEN = getattr(sys, 'frozen', False)
ROOT = os.path.dirname(sys.executable if FROZEN else os.path.abspath(__file__))
VENV = os.path.join(ROOT, '.venv')
VENV_PYTHON = os.path.join(VENV, 'Scripts', 'python.exe')
VENV_PYTHONW = os.path.join(VENV, 'Scripts', 'pythonw.exe')
APPLICATION = os.path.join(ROOT, 'application.pyw')
REQUIREMENTS = os.path.join(ROOT, 'requirements.txt')
MARKER = os.path.join(VENV, 'installed.txt')
LOG = os.path.join(ROOT, 'installation.log')
NO_WINDOW = subprocess.CREATE_NO_WINDOW

ACCENT = '#0969da'


def requirements_hash():
    with open(REQUIREMENTS, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def is_installed():
    if not (os.path.exists(VENV_PYTHONW) and os.path.exists(MARKER)):
        return False
    with open(MARKER) as f:
        return f.read().strip() == requirements_hash()


def launch_application():
    subprocess.Popen([VENV_PYTHONW, APPLICATION], cwd=ROOT, creationflags=NO_WINDOW)


def find_python():
    for cmd in (['py', '-3'], ['python']):
        if not shutil.which(cmd[0]):
            continue
        check = subprocess.run(cmd + ['-c', 'import sys; print(sys.version_info >= (3, 10))'],
                               capture_output=True, text=True, creationflags=NO_WINDOW)
        if check.stdout.strip() == 'True':
            return cmd
    raise RuntimeError("Python 3.10 ou plus récent est introuvable.\n"
                       "Installez-le depuis https://www.python.org puis relancez l'application.")


class Installer:
    STEPS = [
        ('Préparation de Python', 'create_venv'),
        ('Installation des composants (quelques minutes)', 'install_requirements'),
        ('Téléchargement du modèle YOLO26', 'download_model'),
        ('Création du raccourci sur le Bureau', 'create_shortcut'),
    ]

    def __init__(self):
        self.events = queue.Queue()
        self.angle = 0
        self.log = open(LOG, 'w', encoding='utf-8')

        self.root = tk.Tk()
        self.root.title('YOLO Detection — Installation')
        self.root.geometry('480x270')
        self.root.resizable(False, False)
        self.root.configure(bg='white')
        self.root.protocol('WM_DELETE_WINDOW', lambda: None)

        tk.Label(self.root, text='Installation de YOLO Detection', font=('Segoe UI', 14, 'bold'),
                 bg='white').pack(pady=(18, 6))
        self.canvas = tk.Canvas(self.root, width=64, height=64, bg='white', highlightthickness=0)
        self.canvas.pack()
        self.canvas.create_oval(8, 8, 56, 56, outline='#e6e8eb', width=6)
        self.arc = self.canvas.create_arc(8, 8, 56, 56, start=0, extent=90, style='arc',
                                          outline=ACCENT, width=6)
        self.step_label = tk.Label(self.root, text='', font=('Segoe UI', 10), bg='white')
        self.step_label.pack(pady=(10, 4))
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Accent.Horizontal.TProgressbar', background=ACCENT, troughcolor='#e6e8eb',
                        bordercolor='#e6e8eb', lightcolor=ACCENT, darkcolor=ACCENT)
        self.progress = ttk.Progressbar(self.root, length=400, maximum=len(self.STEPS),
                                        style='Accent.Horizontal.TProgressbar')
        self.progress.pack()
        self.detail_label = tk.Label(self.root, text='', font=('Segoe UI', 8), fg='#6e7781', bg='white')
        self.detail_label.pack(pady=(6, 0))

    def run(self):
        threading.Thread(target=self.install, daemon=True).start()
        self.animate()
        self.poll()
        self.root.mainloop()

    def animate(self):
        self.angle = (self.angle - 8) % 360
        extent = 90 + 60 * abs((self.angle % 180) - 90) / 90
        self.canvas.itemconfigure(self.arc, start=self.angle, extent=extent)
        self.root.after(16, self.animate)

    def poll(self):
        while not self.events.empty():
            kind, value = self.events.get()
            if kind == 'step':
                index, label = value
                self.step_label.config(text=f'Étape {index + 1}/{len(self.STEPS)} : {label}…')
                self.progress['value'] = index
                self.detail_label.config(text='')
            elif kind == 'detail':
                self.detail_label.config(text=value[:80])
            elif kind == 'done':
                self.progress['value'] = len(self.STEPS)
                self.step_label.config(text='Installation terminée, ouverture de l\'application…')
                launch_application()
                self.root.after(1500, self.root.destroy)
                return
            elif kind == 'error':
                messagebox.showerror('Installation impossible', f'{value}\n\nDétails : {LOG}')
                self.root.destroy()
                return
        self.root.after(100, self.poll)

    def install(self):
        try:
            for index, (label, method) in enumerate(self.STEPS):
                self.events.put(('step', (index, label)))
                getattr(self, method)()
            with open(MARKER, 'w') as f:
                f.write(requirements_hash())
            self.events.put(('done', None))
        except Exception as e:
            self.log.write(f'\nERREUR : {e}\n')
            self.events.put(('error', str(e)))
        finally:
            self.log.flush()

    def execute(self, cmd):
        self.log.write(f'\n> {" ".join(cmd)}\n')
        process = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, encoding='utf-8', errors='replace', creationflags=NO_WINDOW)
        for line in process.stdout:
            self.log.write(line)
            if line.strip():
                self.events.put(('detail', line.strip()))
        if process.wait() != 0:
            raise RuntimeError(f'La commande a échoué : {" ".join(cmd)}')

    def create_venv(self):
        if not os.path.exists(VENV_PYTHON):
            self.execute(find_python() + ['-m', 'venv', VENV])

    def install_requirements(self):
        self.execute([VENV_PYTHON, '-m', 'pip', 'install', '--disable-pip-version-check', '-r', REQUIREMENTS])

    def download_model(self):
        self.execute([VENV_PYTHON, '-c', 'import detect_utils'])

    def create_shortcut(self):
        target, arguments = (sys.executable, '') if FROZEN else (VENV_PYTHONW, f'"{APPLICATION}"')
        script = ("$s = New-Object -ComObject WScript.Shell;"
                  "$l = $s.CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) 'YOLO Detection.lnk'));"
                  f"$l.TargetPath = '{target}'; $l.Arguments = '{arguments}'; $l.WorkingDirectory = '{ROOT}';"
                  "$l.Save()")
        self.execute(['powershell', '-NoProfile', '-Command', script])


if __name__ == '__main__':
    if is_installed():
        launch_application()
    else:
        Installer().run()
