# YoloProject

Application de bureau de détection d'objets avec YOLO26 (Ultralytics).

## Utilisation

Prérequis : Python 3.10 ou plus récent (https://www.python.org).

Double-cliquer sur **`YOLO Detection.exe`**.

- **Premier lancement** : une fenêtre d'installation s'affiche (quelques minutes). Elle installe les composants,
  télécharge le modèle et crée un raccourci **YOLO Detection** sur le Bureau.
- **Lancements suivants** : l'application s'ouvre directement.

Dans l'application :

- **Choisir une image** (ou glisser-déposer, ou <kbd>Ctrl</kbd>+<kbd>V</kbd>) : affiche l'image avec les objets
  détectés, leur nombre par catégorie et leur confiance.
- **Webcam en direct** : ouvre une fenêtre webcam (touche `q` pour quitter).

## Organisation du projet

```
YoloProject/
├── YOLO Detection.exe      Lanceur : installe, ouvre ou désinstalle l'application
├── requirements.txt        Composants Python installés dans .venv
├── yolo_detection/         Code de l'application
│   ├── paths.py            Tous les emplacements de fichiers (voir ci-dessous)
│   ├── launcher.py         Source de YOLO Detection.exe (installation, lancement, désinstallation)
│   ├── uninstall.py        Liste et supprime ce que l'installation a ajouté
│   ├── desktop.py          Fenêtre de l'application (pywebview)
│   ├── server.py           Serveur de l'interface (Flask)
│   ├── detection.py        Détection YOLO26 et image annotée
│   ├── templates/          Interface (index.html)
│   └── static/             Icône
└── tests/                  Tests et images de test (tests/images/)
```

## Fichiers créés à l'installation et à l'utilisation

Tout reste **dans le dossier du projet**, à deux endroits (ignorés par git) :

| Emplacement | Contenu | Créé quand | Désinstallation |
|---|---|---|---|
| `.venv/` | Environnement Python et composants (~1 Go) | Installation | Supprimé |
| `data/models/yolo26n.pt` | Modèle YOLO26 | Installation | Supprimé |
| `data/logs/installation.log` | Journal de l'installation | Installation | Supprimé |
| `data/logs/application.log` | Journal de l'application | Chaque lancement | Supprimé |
| `data/results/` | Vos analyses : image, image annotée (`_annotated.jpg`) et JSON | Chaque analyse | **Conservé** |

Hors du dossier du projet, un seul élément : le raccourci **YOLO Detection** sur le Bureau (supprimé à la
désinstallation). Les téléchargements de pip passent par son cache habituel (`%LOCALAPPDATA%\pip\Cache`),
partagé avec vos autres projets et donc laissé en place.

## Désinstallation

Dans l'application : menu **⋯** en haut à droite → **Désinstaller l'application…**
(ou lancer `"YOLO Detection.exe" --uninstall`).

La liste exacte de ce qui sera supprimé est affichée avant confirmation (voir le tableau ci-dessus).
Sont conservés : le code du projet, `YOLO Detection.exe`, vos analyses (`data/results`), Python et les
réglages Ultralytics partagés (`%APPDATA%\Ultralytics`). Pour réinstaller, relancer `YOLO Detection.exe`.

## Pour les développeurs

Lancer les tests :

```bash
.venv\Scripts\python -m unittest discover -s tests -v
```

Lancer la version navigateur (http://127.0.0.1:5000) :

```bash
.venv\Scripts\python -m yolo_detection.server
```

Recompiler `YOLO Detection.exe` après une modification de `launcher.py`, `uninstall.py` ou `paths.py`
(avec un Python qui inclut tkinter) :

```bash
py -m pip install pyinstaller
```

```bash
py -m PyInstaller --onefile --noconsole --icon yolo_detection/static/icon.ico --name "YOLO Detection" --paths . --distpath . yolo_detection/launcher.py
```
