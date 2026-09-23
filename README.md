# YoloProject

Application web Flask de détection d'objets avec YOLO26 (Ultralytics).

## Installation

Python 3.10 ou plus récent (testé avec 3.13).

```bash
py -3.13 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Les poids du modèle (`yolo26n.pt`) sont téléchargés automatiquement au premier lancement.

## Lancement

```bash
python app.py
```

Puis ouvrir http://127.0.0.1:5000.

- **Detect Objects in Image** : envoie une image, affiche l'image annotée et la liste des objets détectés.
  Les résultats (image annotée et JSON) sont enregistrés dans `static/results/`.
- **Start Real-Time Video Detection** : ouvre une fenêtre webcam sur la machine qui exécute le serveur (touche `q` pour quitter).
