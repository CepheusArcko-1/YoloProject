import os
import sys
import json
import time
import subprocess
from flask import Flask, request, render_template, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from yolo_detection import paths, uninstall
from yolo_detection.detection import detect_image, detect_webcam

app = Flask(__name__)

UPLOAD_FOLDER = paths.RESULTS
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}


def process_upload(file):
    """Enregistre l'image envoyée, lance la détection et renvoie les données à afficher."""
    stem, ext = os.path.splitext(file.filename)
    ext = ext.lower()
    if ext not in IMAGE_EXTENSIONS:
        raise ValueError('Format non pris en charge (JPG, PNG, BMP ou WEBP attendu).')
    filename = (secure_filename(stem) or 'image') + ext

    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    start = time.perf_counter()
    detections, annotated = detect_image(filepath, UPLOAD_FOLDER)
    duration_ms = round((time.perf_counter() - start) * 1000)

    json_file = os.path.splitext(filename)[0] + '.json'
    with open(os.path.join(UPLOAD_FOLDER, json_file), 'w') as f:
        json.dump(detections, f, indent=2)
    print("Detections:", detections)
    return {'image': filename, 'annotated': annotated, 'json_file': json_file,
            'detections': detections, 'duration_ms': duration_ms}


@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    if request.method == 'POST':
        file = request.files.get('image')
        if file and file.filename:
            try:
                result = process_upload(file)
            except ValueError as e:
                result = {'error': str(e)}
    return render_template('index.html', result=result)

@app.route('/detect', methods=['POST'])
def detect():
    file = request.files.get('image')
    if not file or not file.filename:
        return jsonify(error='Aucune image reçue.'), 400
    try:
        return jsonify(process_upload(file))
    except ValueError as e:
        return jsonify(error=str(e)), 400

@app.route('/start-video')
def start_video():
    detect_webcam()
    return "Video stream finished. Close window to return."

@app.route('/uninstall', methods=['GET'])
def uninstall_items():
    items = uninstall.find_items(paths.ROOT)
    return jsonify(items=[{'label': label, 'size': uninstall.format_size(size)} for label, _, size in items],
                   total=uninstall.format_size(sum(size for _, _, size in items)))

@app.route('/uninstall', methods=['POST'])
def uninstall_app():
    # La désinstallation doit tourner hors de l'environnement .venv qu'elle supprime :
    # on passe par l'exécutable, ou à défaut par le Python de base
    if os.path.exists(paths.EXECUTABLE):
        cmd = [paths.EXECUTABLE]
    else:
        cmd = [getattr(sys, '_base_executable', sys.executable), '-m', 'yolo_detection.launcher']
    # Lancé comme un programme neuf, même si cette application a été ouverte par l'exécutable
    env = {k: v for k, v in os.environ.items() if not k.startswith('_PYI')}
    env['PYINSTALLER_RESET_ENVIRONMENT'] = '1'
    subprocess.Popen(cmd + ['--uninstall', '--confirmed'], cwd=paths.ROOT, env=env,
                     creationflags=subprocess.CREATE_NO_WINDOW)

    # Dans l'application de bureau, application.pyw fournit de quoi fermer la fenêtre
    quit_app = app.config.get('QUIT_APP')
    if quit_app:
        quit_app()
    return jsonify(closing=bool(quit_app))

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.dirname(paths.ICON), os.path.basename(paths.ICON))

@app.route('/results/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
