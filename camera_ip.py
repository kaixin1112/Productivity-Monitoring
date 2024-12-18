from fastapi import FastAPI
from fastapi.responses import StreamingResponse, RedirectResponse
import cv2
import time

# Paths to the model files
FROZEN_GRAPH_PATH = "frozen_inference_graph.pb"
CONFIG_PATH = "ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt"
LABELS_PATH = "coco.names"

# Load the class labels
def load_labels(label_path):
    with open(label_path, 'r') as file:
        labels = {i: line.strip() for i, line in enumerate(file.readlines())}
    return labels

labels = load_labels(LABELS_PATH)

# Load the model
net = cv2.dnn_DetectionModel(FROZEN_GRAPH_PATH, CONFIG_PATH)
net.setInputSize(320, 320)
net.setInputScale(1.0 / 127.5)
net.setInputMean((127.5, 127.5, 127.5))
net.setInputSwapRB(True)

# Initialize FastAPI
app = FastAPI()
camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Replace 0 with your camera source index

def generate_frames():
    fps = 0
    while True:
        success, frame = camera.read()
        if not success:
            break
        
        # Start timer for FPS calculation
        start_time = cv2.getTickCount()

        # Detect objects
        detections = net.detect(frame, confThreshold=0.5)
        class_ids, confidences, boxes = detections if len(detections) == 3 else ([], [], [])

        if len(class_ids) > 0:
            for class_id, confidence, box in zip(class_ids.flatten(), confidences.flatten(), boxes):
                if class_id == 1 and confidence > 0.7:  # Class ID 1 corresponds to "person" in COCO dataset
                    label = f"{labels[class_id]}: {confidence:.2f}"
                    x, y, w, h = box
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Calculate FPS
        end_time = cv2.getTickCount()
        time_taken = (end_time - start_time) / cv2.getTickFrequency()
        fps = 1 / time_taken if time_taken > 0 else 0

        # Display FPS on frame
        fps_label = f"FPS: {fps:.0f}"
        cv2.putText(frame, fps_label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Encode frame as JPEG
        _, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@app.get("/")
def redirect_to_video_feed():
    # Redirect to /video_feed
    return RedirectResponse(url="/video_feed")

@app.get("/video_feed")
def video_feed():
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")