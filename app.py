import os
import json
from flask import Flask, request, render_template, send_from_directory
from detect_utils import detect_image, detect_webcam

app = Flask(__name__)
UPLOAD_FOLDER = 'static/results'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['image']
        if file:
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)
            detections = detect_image(filepath, UPLOAD_FOLDER)
            json_path = os.path.splitext(filepath)[0] + '.json'
            with open(json_path, 'w') as f:
                json.dump(detections, f, indent=2)
            return render_template('index.html', image=file.filename, json_file=os.path.basename(json_path))
    return render_template('index.html', image=None)

@app.route('/start-video')
def start_video():
    detect_webcam()
    return "Video stream finished. Close window to return."

@app.route('/static/results/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
