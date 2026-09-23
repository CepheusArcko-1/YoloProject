# YoloProject

Application de bureau de détection d'objets avec YOLO26 (Ultralytics).

## Installation

1. Télécharger la dernière version dans les
   [Releases](https://github.com/CepheusArcko-1/YoloProject/releases) (`YOLO-Detection-vX.Y.Z.zip`) et la décompresser.
2. Double-cliquer sur **`YOLO Detection.exe`**.

**Rien d'autre à installer, pas même Python.** Au premier lancement, une fenêtre d'installation (quelques minutes)
télécharge Python et les composants, puis le modèle, et crée un raccourci **YOLO Detection** sur le Bureau.
Si une carte graphique NVIDIA est présente, la version de PyTorch qui l'utilise est installée automatiquement.
Les lancements suivants ouvrent directement l'application.

## Fonctionnalités

- **Analyser une ou plusieurs images** : bouton, glisser-déposer (fichiers ou dossiers entiers) ou
  <kbd>Ctrl</kbd>+<kbd>V</kbd>. Les objets sont encadrés, comptés par catégorie et filtrables par confiance.
- **Choix du modèle** en haut : *Rapide*, *Équilibré* ou *Précis* (téléchargé à la première sélection).
  Le matériel utilisé (processeur ou carte graphique) est affiché à côté.
- **Historique** : toutes les analyses sont conservées, rouvrables et supprimables.
- **Export CSV** d'une analyse, d'un lot ou de tout l'historique, directement lisible dans Excel.
- **Webcam en direct** : détection en temps réel dans une fenêtre dédiée (touche `q` pour quitter).
- Fonctionne **sans Internet** une fois installé.

## Fichiers créés à l'installation et à l'utilisation

Tout reste **dans le dossier de l'application** (ces dossiers sont ignorés par git) :

| Emplacement | Contenu | Créé quand | Désinstallation |
|---|---|---|---|
| `runtime/` | Python embarqué et composants (~1 Go) | Installation | Supprimé |
| `data/models/` | Modèles YOLO26 | Installation, puis au choix d'un autre modèle | Supprimé |
| `data/settings.json` | Modèle choisi | Au premier changement de modèle | Supprimé |
| `data/logs/` | Journaux d'installation et d'exécution | Installation, chaque lancement | Supprimé |
| `data/results/<analyse>/` | Une analyse : image d'origine, image annotée, miniature, `analysis.json` | Chaque analyse | **Conservé** |

Hors du dossier, un seul élément : le raccourci **YOLO Detection** sur le Bureau (supprimé à la désinstallation).

## Désinstallation

Dans l'application : menu **⋯** en haut à droite → **Désinstaller l'application…**
(ou lancer `"YOLO Detection.exe" --uninstall`). La liste exacte de ce qui sera supprimé est affichée avant
confirmation. Vos analyses (`data/results`) sont conservées. Pour réinstaller, relancer `YOLO Detection.exe`.

## Organisation du code

```
YoloProject/
├── requirements.txt         Composants installés dans runtime/
├── .github/workflows/       Tests automatiques et publication des versions
├── yolo_detection/
│   ├── paths.py             Tous les emplacements de fichiers
│   ├── launcher.py          Source de YOLO Detection.exe (installation, lancement, désinstallation)
│   ├── uninstall.py         Liste et supprime ce que l'installation a ajouté
│   ├── desktop.py           Fenêtre de l'application (pywebview)
│   ├── server.py            Serveur de l'interface (Flask)
│   ├── detection.py         Modèles YOLO26, carte graphique, images annotées, webcam
│   ├── history.py           Historique des analyses et export CSV
│   ├── labels.py            Noms français des catégories
│   ├── templates/           Page de l'interface
│   └── static/              Style, script, icône et police Inter (embarquée)
└── tests/                   Tests et images de test
```

## Pour les développeurs

Après une première installation (qui crée `runtime/`) :

```bash
runtime\python.exe -m unittest discover -s tests -v
```

```bash
runtime\python.exe -m yolo_detection.server
```

La seconde commande lance la version navigateur sur http://127.0.0.1:5000.

**Publier une version** : GitHub Actions lance les tests, compile `YOLO Detection.exe` et publie l'archive
dans les Releases dès qu'une étiquette de version est poussée :

```bash
git tag v1.0.0
```

```bash
git push origin v1.0.0
```

Les tests tournent aussi automatiquement à chaque push sur `main` et à chaque pull request.

Compiler l'exécutable en local (avec un Python qui inclut tkinter) :

```bash
py -m PyInstaller --onefile --noconsole --icon yolo_detection/static/icon.ico --name "YOLO Detection" --paths . --distpath . yolo_detection/launcher.py
```
