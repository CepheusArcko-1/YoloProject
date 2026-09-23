"""Détection YOLO26 : choix du modèle, carte graphique si disponible, images annotées."""
import os
import threading

import cv2
import numpy as np
import torch
from ultralytics import YOLO

from yolo_detection import paths

# Modèles proposés, du plus rapide au plus précis (téléchargés à la première utilisation)
MODELS = {
    'yolo26n': {'label': 'Rapide', 'description': 'Le plus léger, idéal sur processeur'},
    'yolo26s': {'label': 'Équilibré', 'description': 'Plus précis, un peu plus lent'},
    'yolo26m': {'label': 'Précis', 'description': 'Le plus précis, conseillé avec une carte graphique'},
}
DEFAULT_MODEL = 'yolo26n'

# Couleurs des cadres, partagées par l'image annotée et l'interface
PALETTE = ['#6366f1', '#f43f5e', '#10b981', '#f59e0b', '#0ea5e9', '#a855f7', '#ef4444', '#14b8a6',
           '#eab308', '#ec4899', '#22c55e', '#3b82f6', '#f97316', '#8b5cf6', '#06b6d4', '#84cc16']

_loaded = {}
_lock = threading.Lock()


def _device():
    if torch.cuda.is_available():
        return 'cuda:0'
    if hasattr(torch, 'xpu') and torch.xpu.is_available():
        return 'xpu'
    return 'cpu'


DEVICE = _device()


def device_label():
    if DEVICE.startswith('cuda'):
        return f'Carte graphique ({torch.cuda.get_device_name(0)})'
    if DEVICE == 'xpu':
        return 'Carte graphique Intel'
    return 'Processeur'


def model_path(name):
    return os.path.join(paths.MODELS, name + '.pt')


def is_downloaded(name):
    return os.path.isfile(model_path(name))


def get_model(name):
    """Charge le modèle (en le téléchargeant si besoin) et le garde en mémoire."""
    if name not in MODELS:
        raise ValueError(f'Modèle inconnu : {name}')
    with _lock:
        if name not in _loaded:
            os.makedirs(paths.MODELS, exist_ok=True)
            _loaded[name] = YOLO(model_path(name))
        return _loaded[name]


def warm_up(name):
    """Charge le modèle et fait une première détection à vide : la première vraie analyse est alors immédiate."""
    get_model(name)(np.zeros((64, 64, 3), dtype=np.uint8), device=DEVICE, verbose=False)


def class_color(class_id):
    return PALETTE[class_id % len(PALETTE)]


def _bgr(hex_color):
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return b, g, r


def _text_bgr(hex_color):
    b, g, r = _bgr(hex_color)
    return (20, 20, 20) if 0.299 * r + 0.587 * g + 0.114 * b > 150 else (255, 255, 255)


def annotate(image, detections):
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


def _parse(result, model):
    detections = []
    for box in result.boxes:
        class_id = int(box.cls)
        detections.append({
            'class': model.names[class_id],
            'class_id': class_id,
            'confidence': float(box.conf),
            'bounding_box': [float(x) for x in box.xyxy[0]],
            'color': class_color(class_id),
        })
    return detections


def save_jpeg(path, image):
    # cv2.imwrite ne gère pas les chemins avec accents sous Windows : on encode puis on écrit nous-mêmes
    ok, data = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 92])
    if not ok:
        raise ValueError("Impossible d'encoder l'image")
    with open(path, 'wb') as f:
        f.write(data.tobytes())


def detect_image(image_path, model_name=DEFAULT_MODEL):
    """Renvoie (détections, image d'origine, image annotée) ; les images sont des tableaux BGR."""
    model = get_model(model_name)
    result = model(image_path, device=DEVICE, verbose=False)[0]
    detections = _parse(result, model)
    return detections, result.orig_img, annotate(result.orig_img.copy(), detections)


def detect_webcam(model_name=DEFAULT_MODEL):
    model = get_model(model_name)
    title = 'YOLO Detection - webcam (q pour quitter)'
    cap = cv2.VideoCapture(0)
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            detections = _parse(model(frame, device=DEVICE, verbose=False)[0], model)
            cv2.imshow(title, annotate(frame, detections))
            # Touche q ou fermeture de la fenêtre
            if cv2.waitKey(1) & 0xFF == ord('q') or cv2.getWindowProperty(title, cv2.WND_PROP_VISIBLE) < 1:
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
