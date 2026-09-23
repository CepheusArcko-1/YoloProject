# YoloProject

Application de bureau de détection d'objets avec YOLO26 (Ultralytics).

## Utilisation

Prérequis : Python 3.10 ou plus récent (https://www.python.org).

Double-cliquer sur **`YOLO Detection.exe`**.

- **Premier lancement** : une fenêtre d'installation s'affiche (quelques minutes). Elle installe les composants,
  télécharge le modèle `yolo26n.pt` et crée un raccourci **YOLO Detection** sur le Bureau.
- **Lancements suivants** : l'application s'ouvre directement.

Dans l'application :

- **Analyser une image…** : choisir une image, l'application affiche l'image annotée et la liste des objets détectés.
  Les résultats (image annotée et JSON) sont enregistrés dans `static/results/` (créé automatiquement).
- **Détection webcam en direct** : ouvre une fenêtre webcam (touche `q` pour quitter).

En cas de problème : `installation.log` (installation) et `application.log` (application).

## Pour les développeurs

| Fichier | Rôle |
|---|---|
| `launcher.py` | Source de `YOLO Detection.exe` : installation puis lancement |
| `application.pyw` | Fenêtre de l'application (pywebview) |
| `app.py` | Serveur Flask (interface) |
| `detect_utils.py` | Détection YOLO26 |

Lancer les tests :

```bash
.venv\Scripts\python -m unittest discover -s tests -v
```

Lancer la version navigateur (http://127.0.0.1:5000) :

```bash
.venv\Scripts\python app.py
```

Recompiler `YOLO Detection.exe` après une modification de `launcher.py` (avec un Python qui inclut tkinter) :

```bash
py -m pip install pyinstaller
```

```bash
py -m PyInstaller --onefile --noconsole --name "YOLO Detection" --distpath . launcher.py
```
