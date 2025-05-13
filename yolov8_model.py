from ultralytics import YOLO
import cv2
import json
import os

model = YOLO('yolov8n.pt')

def detect_objects(image_path, output_path):
    results = model(image_path)
    results[0].save(output_path)
    detections = parse_results(results[0])
    return detections

def parse_results(result):
    parsed = []
    for box in result.boxes:
        parsed.append({
            "class": result.names[int(box.cls)],
            "confidence": float(box.conf),
            "bounding_box": [float(x) for x in box.xyxy[0]]
        })
    return parsed

def detect_video(save_dir='static/video/'):
    os.makedirs(save_dir, exist_ok=True)
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        results = model(frame)
        annotated_frame = results[0].plot()
        cv2.imshow('YOLOv8 - Real-Time Video', annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()
