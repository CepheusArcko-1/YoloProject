import torch
import json
import os
import cv2

model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)

def detect_image(image_path, output_folder):
    results = model(image_path)
    
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    custom_output_dir = output_folder

    results.save(save_dir=custom_output_dir)
    
    generated_file = os.path.join(custom_output_dir, base_name + ".jpg")
    annotated_file = os.path.join(custom_output_dir, base_name + "_annotated.jpg")
    if os.path.exists(generated_file):
        os.rename(generated_file, annotated_file)

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
