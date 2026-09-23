"""Historique des analyses : chaque analyse est un dossier data/results/<id>/ contenant
l'image d'origine, l'image annotée, une miniature et analysis.json (détections et informations)."""
import csv
import io
import json
import os
import re
import secrets
import shutil
import time
from datetime import datetime

import cv2
import numpy as np

from yolo_detection import labels, paths
from yolo_detection.detection import MODELS, annotate, class_color, detect_image, device_label, save_jpeg

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
RECORD = 'analysis.json'
ANNOTATED = 'annotated.jpg'
THUMBNAIL = 'thumbnail.jpg'
THUMBNAIL_WIDTH = 360
ID_PATTERN = re.compile(r'^\d{8}-\d{6}-[0-9a-f]{4}$')


def _new_id(when):
    return f'{when:%Y%m%d-%H%M%S}-{secrets.token_hex(2)}'


def _read_image(path):
    # np.fromfile + imdecode : fonctionne aussi avec les chemins accentués sous Windows
    image = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Impossible de lire cette image : le fichier est peut-être endommagé.")
    return image


def _thumbnail(image):
    h, w = image.shape[:2]
    if w <= THUMBNAIL_WIDTH:
        return image
    return cv2.resize(image, (THUMBNAIL_WIDTH, round(h * THUMBNAIL_WIDTH / w)), interpolation=cv2.INTER_AREA)


def folder(analysis_id):
    """Dossier d'une analyse existante ; refuse tout identifiant qui n'en est pas un."""
    if not ID_PATTERN.match(analysis_id or ''):
        raise KeyError(analysis_id)
    path = os.path.join(paths.RESULTS, analysis_id)
    if not os.path.isfile(os.path.join(path, RECORD)):
        raise KeyError(analysis_id)
    return path


def _write(record):
    with open(os.path.join(paths.RESULTS, record['id'], RECORD), 'w', encoding='utf-8') as f:
        json.dump(record, f, ensure_ascii=False, indent=2)


def create(file_storage, model_name):
    """Enregistre l'image envoyée, lance la détection et renvoie l'analyse complète."""
    name = os.path.basename(file_storage.filename or '')
    ext = os.path.splitext(name)[1].lower()
    if ext not in IMAGE_EXTENSIONS:
        raise ValueError('Format non pris en charge (JPG, PNG, BMP ou WEBP attendu).')

    created = datetime.now()
    analysis_id = _new_id(created)
    path = os.path.join(paths.RESULTS, analysis_id)
    os.makedirs(path)
    try:
        original = 'original' + ext
        file_storage.save(os.path.join(path, original))
        _read_image(os.path.join(path, original))

        start = time.perf_counter()
        detections, image, annotated = detect_image(os.path.join(path, original), model_name)
        duration_ms = round((time.perf_counter() - start) * 1000)

        save_jpeg(os.path.join(path, ANNOTATED), annotated)
        save_jpeg(os.path.join(path, THUMBNAIL), _thumbnail(annotated))
    except Exception:
        shutil.rmtree(path, ignore_errors=True)
        raise

    record = {
        'id': analysis_id,
        'name': name,
        'created': created.isoformat(timespec='seconds'),
        'model': model_name,
        'model_label': MODELS[model_name]['label'],
        'device': device_label(),
        'duration_ms': duration_ms,
        'width': int(image.shape[1]),
        'height': int(image.shape[0]),
        'original': original,
        'detections': detections,
    }
    _write(record)
    return record


def get(analysis_id):
    with open(os.path.join(folder(analysis_id), RECORD), encoding='utf-8') as f:
        return json.load(f)


def summary(record):
    counts = {}
    for d in record['detections']:
        counts[d['class']] = counts.get(d['class'], 0) + 1
    return {key: record[key] for key in ('id', 'name', 'created', 'model_label')} | {
        'count': len(record['detections']),
        'classes': sorted(counts.items(), key=lambda item: -item[1]),
    }


def list_all():
    records = []
    if os.path.isdir(paths.RESULTS):
        for entry in os.listdir(paths.RESULTS):
            try:
                records.append(get(entry))
            except (KeyError, OSError, ValueError):
                continue
    return sorted(records, key=lambda r: r['created'], reverse=True)


def delete(analysis_id):
    shutil.rmtree(folder(analysis_id))


def export_csv(analysis_ids):
    """CSV au format attendu par Excel en français : séparateur « ; », virgule décimale, UTF-8 avec BOM."""
    out = io.StringIO()
    out.write('﻿')  # BOM : Excel reconnaît l'UTF-8
    writer = csv.writer(out, delimiter=';', lineterminator='\r\n')
    writer.writerow(['Analyse', 'Fichier', 'Date', 'Modèle', 'Objet', 'Catégorie (anglais)', 'Confiance (%)',
                     'x1', 'y1', 'x2', 'y2'])
    decimal = lambda value: f'{value:.1f}'.replace('.', ',')
    for analysis_id in analysis_ids:
        try:
            record = get(analysis_id)
        except KeyError:
            continue  # analyse supprimée entre-temps
        date = record['created'].replace('T', ' ')
        if not record['detections']:
            writer.writerow([record['id'], record['name'], date, record['model_label'], '', '', '', '', '', '', ''])
        for d in sorted(record['detections'], key=lambda d: -d['confidence']):
            writer.writerow([record['id'], record['name'], date, record['model_label'], labels.french(d['class']),
                             d['class'], decimal(d['confidence'] * 100), *(decimal(v) for v in d['bounding_box'])])
    return out.getvalue()


def migrate_legacy():
    """Convertit les anciennes analyses (fichiers « nom.jpg / nom_annotated.jpg / nom.json » posés
    directement dans data/results) au format un dossier par analyse."""
    if not os.path.isdir(paths.RESULTS):
        return
    coco = list(labels.FRENCH)
    for entry in os.listdir(paths.RESULTS):
        json_path = os.path.join(paths.RESULTS, entry)
        if not (entry.endswith('.json') and os.path.isfile(json_path)):
            continue
        stem = entry[:-5]
        originals = [f for f in os.listdir(paths.RESULTS)
                     if os.path.splitext(f)[0] == stem and os.path.splitext(f)[1].lower() in IMAGE_EXTENSIONS]
        try:
            with open(json_path, encoding='utf-8') as f:
                detections = json.load(f)
            if not originals or not isinstance(detections, list):
                continue
            original_path = os.path.join(paths.RESULTS, originals[0])
            image = _read_image(original_path)
        except (OSError, ValueError):
            continue

        created = datetime.fromtimestamp(os.path.getmtime(json_path))
        analysis_id = _new_id(created)
        path = os.path.join(paths.RESULTS, analysis_id)
        os.makedirs(path)
        for d in detections:
            d.setdefault('class_id', coco.index(d['class']) if d['class'] in coco else 0)
            d.setdefault('color', class_color(d['class_id']))
        ext = os.path.splitext(originals[0])[1].lower()
        shutil.move(original_path, os.path.join(path, 'original' + ext))
        annotated_path = os.path.join(paths.RESULTS, stem + '_annotated.jpg')
        if os.path.isfile(annotated_path):
            shutil.move(annotated_path, os.path.join(path, ANNOTATED))
        annotated = annotate(image.copy(), detections)
        if not os.path.isfile(os.path.join(path, ANNOTATED)):
            save_jpeg(os.path.join(path, ANNOTATED), annotated)
        save_jpeg(os.path.join(path, THUMBNAIL), _thumbnail(annotated))
        _write({
            'id': analysis_id, 'name': originals[0], 'created': created.isoformat(timespec='seconds'),
            'model': 'yolo26n', 'model_label': MODELS['yolo26n']['label'], 'device': None,
            'duration_ms': None, 'width': int(image.shape[1]), 'height': int(image.shape[0]),
            'original': 'original' + ext, 'detections': detections,
        })
        os.remove(json_path)
