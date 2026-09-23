# YoloProject

Application de bureau de détection d'objets avec YOLO26 (Ultralytics).

## Installation (une seule fois)

Prérequis : Python 3.10 ou plus récent (https://www.python.org).

Double-cliquer sur **`installer.bat`**. Il crée l'environnement Python, installe les dépendances
et ajoute un raccourci **YOLO Detection** sur le Bureau et dans ce dossier.

## Utilisation

Double-cliquer sur le raccourci **YOLO Detection**. L'application s'ouvre dans sa propre fenêtre :

- **Analyser une image…** : choisir une image, l'application affiche l'image annotée et la liste des objets détectés.
  Les résultats (image annotée et JSON) sont enregistrés dans `static/results/` (créé automatiquement).
- **Détection webcam en direct** : ouvre une fenêtre webcam (touche `q` pour quitter).

Le modèle `yolo26n.pt` est téléchargé automatiquement au premier lancement.
En cas de problème, les messages de l'application sont dans `application.log`.

## Tests

Double-cliquer sur **`tester.bat`** pour vérifier que la détection fonctionne.

## Pour les développeurs

Lancer la version navigateur (http://127.0.0.1:5000) avec rechargement automatique :

```bash
.venv\Scripts\python app.py
```
