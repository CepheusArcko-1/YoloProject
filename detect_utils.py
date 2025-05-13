import torch
import json
import os
import cv2

model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)

def detect_image(image_path, output_folder):
    results = model(image_path)

    annotated_image = results.render()[0] 

    output_image_path = os.path.join(output_folder, os.path.basename(image_path))

    cv2.imwrite(output_image_path, annotated_image)

    parsed_results = []
    for result in results.xyxy:
        for *box, conf, cls in result:
            parsed_results.append({
                'class': model.names[int(cls)],
                'confidence': float(conf),
                'bounding_box': [float(x) for x in box]
            })
    return parsed_results



def detect_webcam():
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        results = model(frame)
        annotated_frame = results.render()[0]
        cv2.imshow('YOLOv5 Webcam Detection', annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()
