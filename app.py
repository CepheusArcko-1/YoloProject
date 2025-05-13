import os
from flask import Flask, request, render_template, send_from_directory
from yolov8_model import detect_objects

app = Flask(__name__)
UPLOAD_FOLDER = 'static/results'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['image']
        if file:
            image_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(image_path)
            detect_objects(image_path, UPLOAD_FOLDER)
            return render_template('index.html', image=file.filename)
    return render_template('index.html', image=None)

@app.route('/static/results/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
