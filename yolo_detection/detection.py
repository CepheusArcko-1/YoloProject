import os
import cv2
from ultralytics import YOLO

from yolo_detection import paths

os.makedirs(paths.MODELS, exist_ok=True)
model = YOLO(paths.MODEL)

# Couleurs des cadres, partagées par l'image annotée et l'interface
PALETTE = ['#6366f1', '#f43f5e', '#10b981', '#f59e0b', '#0ea5e9', '#a855f7', '#ef4444', '#14b8a6',
           '#eab308', '#ec4899', '#22c55e', '#3b82f6', '#f97316', '#8b5cf6', '#06b6d4', '#84cc16']


def class_color(class_id):
    return PALETTE[class_id % len(PALETTE)]


def _bgr(hex_color):
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return b, g, r


def _text_bgr(hex_color):
    b, g, r = _bgr(hex_color)
    return (20, 20, 20) if 0.299 * r + 0.587 * g + 0.114 * b > 150 else (255, 255, 255)


def _annotate(image, detections):
    thickness = max(2, round(max(image.shape[:2]) / 400))
    scale = thickness / 3.5
    for d in detections:
        x1, y1, x2, y2 = (int(v) for v in d['bounding_box'])
        color = _bgr(d['color'])
        cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness, cv2.LINE_AA)
        text = f"{d['class']} {d['confidence']:.0%}"
        (tw, th), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, max(1, thickness // 2))
        top = y1 - th - baseline - 6 if y1 - th - baseline - 6 >= 0 else y1
        cv2.rectangle(image, (x1, top), (x1 + tw + 8, top + th + baseline + 6), color, -1)
        cv2.putText(image, text, (x1 + 4, top + th + 3), cv2.FONT_HERSHEY_SIMPLEX, scale,
                    _text_bgr(d['color']), max(1, thickness // 2), cv2.LINE_AA)
    return image


def detect_image(image_path, output_folder):
    result = model(image_path)[0]

    parsed_results = []
    for box in result.boxes:
        class_id = int(box.cls)
        parsed_results.append({
            'class': model.names[class_id],
            'class_id': class_id,
            'confidence': float(box.conf),
            'bounding_box': [float(x) for x in box.xyxy[0]],
            'color': class_color(class_id),
        })

    base_name = os.path.splitext(os.path.basename(image_path))[0]
    annotated_file = os.path.join(output_folder, base_name + '_annotated.jpg')
    cv2.imwrite(annotated_file, _annotate(result.orig_img.copy(), parsed_results))
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
