import os
import cv2
from ultralytics import YOLO

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'yolo26n.pt')
model = YOLO(MODEL_PATH)


def detect_image(image_path, output_folder):
    result = model(image_path)[0]

    base_name = os.path.splitext(os.path.basename(image_path))[0]
    annotated_file = os.path.join(output_folder, base_name + '_annotated.jpg')
    cv2.imwrite(annotated_file, result.plot())

    parsed_results = []
    for box in result.boxes:
        parsed_results.append({
            'class': model.names[int(box.cls)],
            'confidence': float(box.conf),
            'bounding_box': [float(x) for x in box.xyxy[0]]
        })
    return parsed_results, os.path.basename(annotated_file)


def detect_webcam():
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        annotated_frame = model(frame, verbose=False)[0].plot()
        cv2.imshow('YOLO26 Webcam Detection (q pour quitter)', annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()
