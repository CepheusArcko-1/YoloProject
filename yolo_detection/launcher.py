"""Lanceur de YOLO Detection : installe l'application au premier lancement, puis l'ouvre.

« YOLO Detection.exe --uninstall » retire ce que l'installation a ajouté (voir uninstall.py).
Compilé en « YOLO Detection.exe » (voir README). N'utilise que la bibliothèque standard.
"""
import ctypes
import hashlib
import os
import queue
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox

from yolo_detection import paths, uninstall

FROZEN = getattr(sys, 'frozen', False)
NO_WINDOW = subprocess.CREATE_NO_WINDOW


def windows_dark_mode():
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r'Software\Microsoft\Windows\CurrentVersion\Themes\Personalize')
        return winreg.QueryValueEx(key, 'AppsUseLightTheme')[0] == 0
    except OSError:
        return False


# Mêmes couleurs que l'interface de l'application
THEME = ({'bg': '#0e1015', 'text': '#eceef2', 'muted': '#9aa1ad', 'track': '#2a2f3a', 'accent': '#818cf8',
          'accent_hover': '#a5b4fc', 'button': '#1f232c', 'button_hover': '#2a2f3a', 'done': '#34d399',
          'danger': '#ef4444', 'danger_hover': '#f87171'}
         if windows_dark_mode() else
         {'bg': '#f5f6f8', 'text': '#16181d', 'muted': '#6b7280', 'track': '#e3e6ea', 'accent': '#4f46e5',
          'accent_hover': '#4338ca', 'button': '#ffffff', 'button_hover': '#eceef2', 'done': '#10b981',
          'danger': '#dc2626', 'danger_hover': '#b91c1c'})


def requirements_hash():
    with open(paths.REQUIREMENTS, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def is_installed():
    if not (os.path.exists(paths.VENV_PYTHONW) and os.path.exists(paths.INSTALLED_MARKER)):
        return False
    with open(paths.INSTALLED_MARKER) as f:
        return f.read().strip() == requirements_hash()


def launch_application():
    # L'application ne doit pas hériter des variables internes de l'exécutable PyInstaller,
    # sinon elle ne pourrait pas relancer l'exécutable plus tard (désinstallation)
    env = {k: v for k, v in os.environ.items() if not k.startswith('_PYI')}
    env['PYINSTALLER_RESET_ENVIRONMENT'] = '1'
    subprocess.Popen([paths.VENV_PYTHONW, '-m', 'yolo_detection.desktop'], cwd=paths.ROOT, env=env,
                     creationflags=NO_WINDOW)


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


class ThemedWindow:
    """Fenêtre aux couleurs de l'application, avec le logo entouré d'un anneau animé."""

    def __init__(self, title, size):
        t = THEME
        self.events = queue.Queue()
        self.angle = 0
        self.spinning = True

        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry(size)
        self.root.resizable(False, False)
        self.root.configure(bg=t['bg'])
        if os.path.exists(paths.ICON):
            self.root.iconbitmap(paths.ICON)
        if windows_dark_mode():
            self.root.update_idletasks()
            hwnd = int(self.root.wm_frame(), 16)
            dark = ctypes.c_int(1)  # DWMWA_USE_IMMERSIVE_DARK_MODE = 20 : barre de titre sombre
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(dark), ctypes.sizeof(dark))

        self.canvas = tk.Canvas(self.root, width=110, height=110, bg=t['bg'], highlightthickness=0)
        self.canvas.pack(pady=(26, 8))
        self.canvas.create_oval(6, 6, 104, 104, outline=t['track'], width=4)
        self.arc = self.canvas.create_arc(6, 6, 104, 104, start=0, extent=90, style='arc',
                                          outline=t['accent'], width=4)
        self.draw_logo(25, 25, 60)

        self.title_label = tk.Label(self.root, text='', font=('Segoe UI Semibold', 15), fg=t['text'], bg=t['bg'])
        self.title_label.pack()
        self.subtitle_label = tk.Label(self.root, text='', font=('Segoe UI', 9), fg=t['muted'], bg=t['bg'],
                                       wraplength=440, justify='center')
        self.subtitle_label.pack(pady=(2, 14))

    def draw_logo(self, x, y, size):
        """Carré arrondi violet avec un cadre de détection blanc, comme l'icône."""
        r = size * 0.24
        points = [x + r, y, x + size - r, y, x + size, y, x + size, y + r, x + size, y + size - r,
                  x + size, y + size, x + size - r, y + size, x + r, y + size, x, y + size,
                  x, y + size - r, x, y + r, x, y]
        self.canvas.create_polygon(points, smooth=True, fill='#6d5cf5', outline='')
        m, length, w = size * 0.24, size * 0.17, max(2, size / 14)
        for cx, cy, dx, dy in ((x + m, y + m, 1, 1), (x + size - m, y + m, -1, 1),
                               (x + m, y + size - m, 1, -1), (x + size - m, y + size - m, -1, -1)):
            self.canvas.create_line(cx, cy + dy * length, cx, cy, cx + dx * length, cy,
                                    fill='white', width=w, capstyle='round', joinstyle='round')
        c, d = x + size / 2, size * 0.09
        self.canvas.create_oval(c - d, y + size / 2 - d, c + d, y + size / 2 + d, fill='white', outline='')

    def step_row(self, parent, label, detail=''):
        t = THEME
        row = tk.Frame(parent, bg=t['bg'])
        row.pack(fill='x', pady=2)
        icon = tk.Label(row, text='○', width=2, font=('Segoe UI Symbol', 10), fg=t['muted'], bg=t['bg'])
        icon.pack(side='left')
        text = tk.Label(row, text=label, font=('Segoe UI', 10), fg=t['muted'], bg=t['bg'])
        text.pack(side='left')
        if detail:
            tk.Label(row, text=detail, font=('Segoe UI', 9), fg=t['muted'], bg=t['bg']).pack(side='right')
        return icon, text

    def mark_rows(self, rows, current):
        t = THEME
        for i, (icon, text) in enumerate(rows):
            if i < current:
                icon.config(text='✓', fg=t['done'])
                text.config(fg=t['text'], font=('Segoe UI', 10))
            elif i == current:
                icon.config(text='●', fg=t['accent'])
                text.config(fg=t['text'], font=('Segoe UI Semibold', 10))
            else:
                icon.config(text='○', fg=t['muted'])
                text.config(fg=t['muted'], font=('Segoe UI', 10))

    def button(self, parent, text, command, primary=False, danger=False):
        t = THEME
        if danger:
            bg, hover, fg = t['danger'], t['danger_hover'], '#ffffff'
        elif primary:
            bg, hover, fg = t['accent'], t['accent_hover'], '#ffffff'
        else:
            bg, hover, fg = t['button'], t['button_hover'], t['text']
        b = tk.Button(parent, text=text, command=command, font=('Segoe UI Semibold', 10), fg=fg, bg=bg,
                      activebackground=hover, activeforeground=fg, relief='flat', bd=0, padx=18, pady=7,
                      cursor='hand2', highlightthickness=1, highlightbackground=t['track'])
        b.bind('<Enter>', lambda e: b.config(bg=hover))
        b.bind('<Leave>', lambda e: b.config(bg=bg))
        return b

    def animate(self):
        if self.spinning:
            self.angle = (self.angle - 8) % 360
            extent = 90 + 60 * abs((self.angle % 180) - 90) / 90
            self.canvas.itemconfigure(self.arc, start=self.angle, extent=extent)
        self.tick()
        self.root.after(16, self.animate)

    def tick(self):
        pass

    def stop_spinner(self, color):
        self.spinning = False
        # Un arc de 360° ne s'affiche pas : on remplace l'anneau par un cercle complet
        self.canvas.itemconfigure(self.arc, extent=0)
        self.canvas.create_oval(6, 6, 104, 104, outline=color, width=4)


class Installer(ThemedWindow):
    STEPS = [
        ('Préparation de Python', 'create_venv'),
        ('Installation des composants (quelques minutes)', 'install_requirements'),
        ('Téléchargement du modèle YOLO26', 'download_model'),
        ('Création du raccourci sur le Bureau', 'create_shortcut'),
    ]

    def __init__(self):
        super().__init__('YOLO Detection — Installation', '520x400')
        t = THEME
        self.current = -1
        os.makedirs(paths.LOGS, exist_ok=True)
        self.log = open(paths.INSTALL_LOG, 'w', encoding='utf-8')
        self.root.protocol('WM_DELETE_WINDOW', lambda: None)
        self.title_label.config(text='Installation de YOLO Detection')
        self.subtitle_label.config(text='Premier lancement : quelques minutes, une seule fois.')

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Accent.Horizontal.TProgressbar', thickness=6, background=t['accent'],
                        troughcolor=t['track'], bordercolor=t['track'], lightcolor=t['accent'],
                        darkcolor=t['accent'])
        self.progress = ttk.Progressbar(self.root, length=380, maximum=len(self.STEPS) * 100,
                                        style='Accent.Horizontal.TProgressbar')
        self.progress.pack()

        steps = tk.Frame(self.root, bg=t['bg'])
        steps.pack(pady=(14, 0))
        self.step_rows = [self.step_row(steps, label) for label, _ in self.STEPS]

        self.detail_label = tk.Label(self.root, text='', font=('Consolas', 8), fg=t['muted'], bg=t['bg'])
        self.detail_label.pack(pady=(12, 0))

    def run(self):
        threading.Thread(target=self.install, daemon=True).start()
        self.animate()
        self.poll()
        self.root.mainloop()

    def tick(self):
        # La barre avance doucement pendant une étape, sans atteindre l'étape suivante
        if 0 <= self.current < len(self.STEPS):
            ceiling = (self.current + 1) * 100 - 5
            value = self.progress['value']
            self.progress['value'] = value + (ceiling - value) * 0.004

    def poll(self):
        while not self.events.empty():
            kind, value = self.events.get()
            if kind == 'step':
                self.current = value
                self.mark_rows(self.step_rows, value)
                self.progress['value'] = value * 100
                self.detail_label.config(text='')
            elif kind == 'detail':
                self.detail_label.config(text=value[:70])
            elif kind == 'done':
                self.current = len(self.STEPS)
                self.mark_rows(self.step_rows, len(self.STEPS))
                self.progress['value'] = len(self.STEPS) * 100
                self.detail_label.config(text='Installation terminée, ouverture de l\'application…')
                launch_application()
                self.root.after(1500, self.root.destroy)
                return
            elif kind == 'error':
                messagebox.showerror('Installation impossible', f'{value}\n\nDétails : {paths.INSTALL_LOG}')
                self.root.destroy()
                return
        self.root.after(100, self.poll)

    def install(self):
        try:
            for index, (_, method) in enumerate(self.STEPS):
                self.events.put(('step', index))
                getattr(self, method)()
            with open(paths.INSTALLED_MARKER, 'w') as f:
                f.write(requirements_hash())
            self.events.put(('done', None))
        except Exception as e:
            self.log.write(f'\nERREUR : {e}\n')
            self.events.put(('error', str(e)))
        finally:
            self.log.flush()

    def execute(self, cmd):
        self.log.write(f'\n> {" ".join(cmd)}\n')
        process = subprocess.Popen(cmd, cwd=paths.ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, encoding='utf-8', errors='replace', creationflags=NO_WINDOW)
        for line in process.stdout:
            self.log.write(line)
            if line.strip():
                self.events.put(('detail', line.strip()))
        if process.wait() != 0:
            raise RuntimeError(f'La commande a échoué : {" ".join(cmd)}')

    def create_venv(self):
        if not os.path.exists(paths.VENV_PYTHON):
            self.execute(find_python() + ['-m', 'venv', paths.VENV])

    def install_requirements(self):
        self.execute([paths.VENV_PYTHON, '-m', 'pip', 'install', '--disable-pip-version-check',
                      '-r', paths.REQUIREMENTS])

    def download_model(self):
        self.execute([paths.VENV_PYTHON, '-c', 'import yolo_detection.detection'])

    def create_shortcut(self):
        target, arguments = ((sys.executable, '') if FROZEN
                             else (paths.VENV_PYTHONW, '-m yolo_detection.desktop'))
        script = ("$s = New-Object -ComObject WScript.Shell;"
                  f"$l = $s.CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) '{uninstall.SHORTCUT_NAME}'));"
                  f"$l.TargetPath = '{target}'; $l.Arguments = '{arguments}'; $l.WorkingDirectory = '{paths.ROOT}';"
                  "$l.Save()")
        self.execute(['powershell', '-NoProfile', '-Command', script])


class Uninstaller(ThemedWindow):
    """Montre ce qui va être supprimé, demande confirmation (sauf si déjà confirmée dans l'application),
    puis supprime élément par élément."""

    def __init__(self, confirmed=False):
        super().__init__('YOLO Detection — Désinstallation', '540x520')
        t = THEME
        self.items = uninstall.find_items(paths.ROOT)
        self.spinning = False
        self.canvas.itemconfigure(self.arc, extent=0)

        total = uninstall.format_size(sum(size for _, _, size in self.items))
        self.title_label.config(text='Désinstaller YOLO Detection')
        self.subtitle_label.config(
            text=f'Les éléments ci-dessous ont été installés par l\'application ({total}).'
            if self.items else 'Rien à désinstaller : l\'application n\'est pas installée.')

        rows = tk.Frame(self.root, bg=t['bg'])
        rows.pack(fill='x', padx=60)
        self.rows = [self.step_row(rows, label, uninstall.format_size(size)) for label, _, size in self.items]

        tk.Label(self.root, text='Conservés : le code du projet, YOLO Detection.exe, vos résultats d\'analyse '
                                 '(data/results) et Python.',
                 font=('Segoe UI', 9), fg=t['muted'], bg=t['bg'], wraplength=420, justify='center').pack(pady=(14, 0))

        self.buttons = tk.Frame(self.root, bg=t['bg'])
        self.buttons.pack(side='bottom', pady=(0, 24))
        if self.items:
            self.cancel_button = self.button(self.buttons, 'Annuler', self.root.destroy)
            self.cancel_button.pack(side='left', padx=6)
            self.confirm_button = self.button(self.buttons, 'Désinstaller', self.start, danger=True)
            self.confirm_button.pack(side='left', padx=6)
            if confirmed:
                self.root.after(300, self.start)
        else:
            self.button(self.buttons, 'Fermer', self.root.destroy, primary=True).pack()

    def run(self):
        self.animate()
        self.root.mainloop()

    def start(self):
        self.root.protocol('WM_DELETE_WINDOW', lambda: None)
        for child in self.buttons.winfo_children():
            child.destroy()
        self.spinning = True
        self.title_label.config(text='Désinstallation en cours…')
        threading.Thread(target=self.remove_all, daemon=True).start()
        self.poll()

    def remove_all(self):
        for index, (label, path, _) in enumerate(self.items):
            self.events.put(('step', index))
            try:
                uninstall.remove(path)
            except OSError as e:
                self.events.put(('error', f'Impossible de supprimer : {label}\n{e}\n\n'
                                          'Fermez l\'application YOLO Detection puis réessayez.'))
                return
        self.events.put(('done', None))

    def poll(self):
        while not self.events.empty():
            kind, value = self.events.get()
            if kind == 'step':
                self.mark_rows(self.rows, value)
            elif kind == 'done':
                self.mark_rows(self.rows, len(self.rows))
                self.stop_spinner(THEME['done'])
                freed = uninstall.format_size(sum(size for _, _, size in self.items))
                self.title_label.config(text='Désinstallation terminée')
                self.subtitle_label.config(text=f'{freed} libérés. Pour réinstaller, relancez YOLO Detection.exe.')
                self.root.protocol('WM_DELETE_WINDOW', self.root.destroy)
                self.button(self.buttons, 'Fermer', self.root.destroy, primary=True).pack()
                return
            elif kind == 'error':
                self.stop_spinner(THEME['danger'])
                self.title_label.config(text='Désinstallation interrompue')
                messagebox.showerror('Désinstallation impossible', value)
                self.root.destroy()
                return
        self.root.after(100, self.poll)


if __name__ == '__main__':
    if '--uninstall' in sys.argv:
        Uninstaller(confirmed='--confirmed' in sys.argv).run()
    elif is_installed():
        launch_application()
    else:
        Installer().run()
