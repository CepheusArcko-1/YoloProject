"""Serveur de l'interface : analyses, historique, export CSV, réglages, webcam et désinstallation."""
import json
import os
import shutil
import subprocess
import threading

from flask import Flask, Response, jsonify, render_template, request, send_from_directory

from yolo_detection import history, labels, paths, uninstall
from yolo_detection.detection import DEFAULT_MODEL, MODELS, detect_webcam, device_label, get_model, is_downloaded

app = Flask(__name__)

os.makedirs(paths.RESULTS, exist_ok=True)
history.migrate_legacy()

# Une seule webcam à la fois : un second clic ne doit pas ouvrir une deuxième fenêtre
webcam_lock = threading.Lock()


def load_settings():
    try:
        with open(paths.SETTINGS, encoding='utf-8') as f:
            settings = json.load(f)
    except (OSError, ValueError):
        settings = {}
    if settings.get('model') not in MODELS:
        settings['model'] = DEFAULT_MODEL
    return settings


def save_settings(settings):
    os.makedirs(paths.DATA, exist_ok=True)
    with open(paths.SETTINGS, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2)


def settings_payload():
    current = load_settings()['model']
    return {
        'model': current,
        'device': device_label(),
        'models': [{'id': name, **info, 'downloaded': is_downloaded(name)} for name, info in MODELS.items()],
    }


@app.route('/')
def index():
    return render_template('index.html', labels=labels.FRENCH)


@app.route('/detect', methods=['POST'])
def detect():
    file = request.files.get('image')
    if not file or not file.filename:
        return jsonify(error='Aucune image reçue.'), 400
    try:
        return jsonify(history.create(file, load_settings()['model']))
    except ValueError as e:
        return jsonify(error=str(e)), 400


@app.route('/history')
def history_list():
    return jsonify([history.summary(record) for record in history.list_all()])


@app.route('/history/<analysis_id>', methods=['GET', 'DELETE'])
def history_item(analysis_id):
    try:
        if request.method == 'DELETE':
            history.delete(analysis_id)
            return jsonify(deleted=analysis_id)
        return jsonify(history.get(analysis_id))
    except KeyError:
        return jsonify(error='Analyse introuvable.'), 404


@app.route('/results/<analysis_id>/<filename>')
def result_file(analysis_id, filename):
    try:
        return send_from_directory(history.folder(analysis_id), filename)
    except KeyError:
        return jsonify(error='Analyse introuvable.'), 404


@app.route('/export.csv')
def export_csv():
    ids = [i for i in request.args.get('ids', '').split(',') if i]
    content = history.export_csv(ids)
    filename = 'detections.csv' if len(ids) != 1 else f'detections-{ids[0]}.csv'
    return Response(content, mimetype='text/csv',
                    headers={'Content-Disposition': f'attachment; filename="{filename}"'})


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        model = (request.get_json(silent=True) or {}).get('model')
        if model not in MODELS:
            return jsonify(error='Modèle inconnu.'), 400
        get_model(model)  # téléchargé et chargé tout de suite, pour que la prochaine analyse soit rapide
        save_settings(load_settings() | {'model': model})
    return jsonify(settings_payload())


@app.route('/start-video', methods=['POST'])
def start_video():
    if not webcam_lock.acquire(blocking=False):
        return jsonify(error='La webcam est déjà ouverte.'), 409
    try:
        detect_webcam(load_settings()['model'])
    finally:
        webcam_lock.release()
    return jsonify(closed=True)


@app.route('/uninstall', methods=['GET'])
def uninstall_items():
    items = uninstall.find_items(paths.ROOT)
    return jsonify(items=[{'label': label, 'size': uninstall.format_size(size)} for label, _, size in items],
                   total=uninstall.format_size(sum(size for _, _, size in items)))


@app.route('/uninstall', methods=['POST'])
def uninstall_app():
    # La désinstallation supprime le Python qui fait tourner ce serveur : elle passe donc par
    # l'exécutable, ou à défaut (développement) par le Python du système
    if os.path.exists(paths.EXECUTABLE):
        cmd = [paths.EXECUTABLE]
    elif shutil.which('py'):
        cmd = ['py', '-3', '-m', 'yolo_detection.launcher']
    else:
        return jsonify(error='YOLO Detection.exe est introuvable.'), 500
    # Lancé comme un programme neuf, même si cette application a été ouverte par l'exécutable
    env = {k: v for k, v in os.environ.items() if not k.startswith('_PYI')}
    env['PYINSTALLER_RESET_ENVIRONMENT'] = '1'
    subprocess.Popen(cmd + ['--uninstall', '--confirmed'], cwd=paths.ROOT, env=env,
                     creationflags=subprocess.CREATE_NO_WINDOW)

    # Dans l'application de bureau, desktop.py fournit de quoi fermer la fenêtre
    quit_app = app.config.get('QUIT_APP')
    if quit_app:
        quit_app()
    return jsonify(closing=bool(quit_app))


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.dirname(paths.ICON), os.path.basename(paths.ICON))


if __name__ == '__main__':
    app.run(debug=True)
