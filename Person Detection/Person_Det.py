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

# Video capture
cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)  # Use 0 for webcam or provide the path to a video file
# Set video frame size
frame_width = 800
frame_height = 600
cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)

# For calculating FPS
fps = 0
prev_time = time.time()

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Start timer for FPS calculation
    start_time = cv2.getTickCount()

    # Detect objects
    detections = net.detect(frame, confThreshold=0.5)
    class_ids, confidences, boxes = detections if len(detections) == 3 else ([], [], [])

    if len(class_ids) > 0:
        for class_id, confidence, box in zip(class_ids.flatten(), confidences.flatten(), boxes):
            if class_id == 1:  # Class ID 1 corresponds to "person" in COCO dataset
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

    # Show the frame
    cv2.imshow("Person Detection", frame)

    # Condition to close the video frame
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):  # Press 'q' to quit
        break
    if cv2.getWindowProperty('Person Detection', cv2.WND_PROP_VISIBLE) < 1:
        break

cap.release()
cv2.destroyAllWindows()