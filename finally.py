import tkinter as tk
from tkinter import ttk, Button
import multiprocessing
import cv2
import json
from ultralytics import YOLO
from YOLODetector import YOLODetector
from PersonDetector import PersonDetector
import numpy as np
import time

# Load camera data from JSON
def load_camera_data():
    with open("camera_data.json", "r") as file:
        return json.load(file)

# Load step data from JSON
def load_steps_data():
    with open("steps_data.json", "r") as file:
        return json.load(file)

# Populate global steps dictionary
def populate_global_steps(steps_data):
    global_steps = {}
    for idx, step in enumerate(steps_data, start=1):
        camera_index = int(step["Camera"])
        roi = int(step["ROI"].split()[-1])
        obj = step["Object"]
        global_steps[idx] = [camera_index, roi, obj]
    return global_steps

def run_person_detector(camera_index, queue):
    """Standalone function for Person Detection."""
    detector = PersonDetector()
    detector.run(camera_index, queue)

def run_yolo_detector(model_path, camera_index, queue):
    """Standalone function for YOLO Detection."""
    detector = YOLODetector(model_path)
    detector.run(camera_index=camera_index, threshold=0.6, queue=queue)

def process_queues(global_steps, person_queue, yolo_queue, result_queue):
    """Processes queues to validate detections and handle step completions."""
    current_step = 1

    while current_step <= len(global_steps):
        # Get the expected details for the current step
        expected_camera_index, expected_roi, expected_object = global_steps[current_step]

        person_message = None
        yolo_message = None

        # Check both queues for new messages
        if not person_queue.empty():
            person_message = person_queue.get()
        if not yolo_queue.empty():
            yolo_message = yolo_queue.get()

        # Validate detection from PersonDetector
        if person_message:
            if (person_message["camera_index"] == expected_camera_index and
                person_message["roi"] == expected_roi and
                person_message["object"] == expected_object):
                result_queue.put(current_step)
                current_step += 1
                continue

        # Validate detection from YOLODetector
        if yolo_message:
            if (yolo_message["camera_index"] == expected_camera_index and
                yolo_message["roi"] == expected_roi and
                yolo_message["object"] == expected_object):
                result_queue.put(current_step)
                current_step += 1
                continue

def analyze_photo(photo, model_path):
    """Analyze the given photo for object detection."""
    # Load YOLO model
    model = YOLO(model_path)
    
    # Perform detection
    results = model(photo, verbose=False)
    
    # Extract details
    names = results[0].names
    scores = results[0].boxes.conf.cpu().numpy()
    classes = results[0].boxes.cls.cpu().numpy().astype(int)
    boxes = results[0].boxes.xyxy.cpu().numpy().astype(np.int32)
    
    detections = []
    for score, cls, box in zip(scores, classes, boxes):
        if score >= 0.5:  # Confidence threshold
            x1, y1, x2, y2 = box
            detections.append({
                "label": names[cls],
                "confidence": score,
                "bbox": (x1, y1, x2, y2),
            })
    
    return detections

def process_image(camera_index, model_path):
    """Capture and process an image from the specified camera."""
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print(f"Error: Unable to access camera {camera_index}")
        return

    try:
        ret, frame = cap.read()
        if not ret:
            print("Error: Unable to capture frame.")
            return

        # Analyze the captured photo
        detections = analyze_photo(frame, model_path)

        # Check components
        required_components = {"Motor": 2, "Wheel": 2, "Driver": 1, "ESP32": 1}
        for detection in detections:
            label = detection["label"]
            if label in required_components and required_components[label] > 0:
                required_components[label] -= 1

        # Determine pass/fail
        if all(count == 0 for count in required_components.values()):
            cv2.putText(frame, "PASS", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        else:
            cv2.putText(frame, "FAIL", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # Draw bounding boxes
        for detection in detections:
            x1, y1, x2, y2 = detection["bbox"]
            label = detection["label"]
            confidence = detection["confidence"]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"{label}: {confidence:.2f}", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Display the result
        cv2.imshow("Capture Result", frame)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    finally:
        cap.release()

class StepTrackingApp:
    def __init__(self, root, global_steps, camera_data, model_path):
        self.root = root
        self.global_steps = global_steps
        self.camera_data = camera_data
        self.model_path = model_path
        self.completed_steps = []

        # Configure the window
        self.root.title("Step Tracking")
        self.table = ttk.Treeview(root, columns=("Camera Index", "ROI", "Object"), show="headings")
        self.table.heading("Camera Index", text="Camera Index")
        self.table.heading("ROI", text="ROI")
        self.table.heading("Object", text="Object")
        self.table.pack(fill=tk.BOTH, expand=True)

        # Populate the table with global_steps
        for idx, (step, data) in enumerate(global_steps.items(), start=1):
            self.table.insert("", "end", iid=step, values=(data[0], data[1], data[2]))

        # Start camera processes
        self.start_camera_processes()

    def start_camera_processes(self):
        for cam_id, cam_info in self.camera_data.items():
            camera_index = int(cam_info["Camera ID"])
            technique = cam_info["Technique"]

            if technique == "Person Detection":
                process = multiprocessing.Process(target=run_person_detector, args=(camera_index, person_queue))
                process.start()
            elif technique == "Object Detection (Vid)":
                process = multiprocessing.Process(target=run_yolo_detector, args=(self.model_path, camera_index, yolo_queue))
                process.start()

    def highlight_row(self, steps):
        """Highlight the given step rows."""
        for row in self.table.get_children():
            self.table.item(row, tags=())
        self.table.tag_configure("highlight", background="lightblue")
        for step in steps:
            self.table.item(step, tags=("highlight",))

    def update_highlight(self):
        """Update the highlight for completed steps."""
        self.highlight_row(self.completed_steps)

    def mark_complete(self):
        """Highlight the last row and then launch the capture app."""
        self.completed_steps.append(len(self.global_steps))  # Highlight the last row
        self.update_highlight()  # Update the table with the last step highlighted

        # Launch the capture app
        self.root.title("All Steps Completed")
        self.root.after(500, lambda: CaptureApp(self.camera_data, self.model_path))

class CaptureApp:
    def __init__(self, camera_data, model_path):
        self.camera_data = camera_data
        self.model_path = model_path

        # Find camera with Object Detection (Cam)
        for cam_id, cam_info in self.camera_data.items():
            if cam_info["Technique"] == "Object Detection (Cam)":
                self.camera_index = int(cam_info["Camera ID"])
                self.launch_camera_window()

    def launch_camera_window(self):
        """Open OpenCV window with a capture button."""
        while True:
            cap = cv2.VideoCapture(self.camera_index)

            if not cap.isOpened():
                print("Error: Unable to access camera.")
                return

            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Error: Unable to read from camera.")
                    break

                cv2.imshow("Object Detection (Cam)", frame)

                if cv2.waitKey(1) & 0xFF == ord('c'):  # 'c' for capture
                    cap.release()
                    cv2.destroyAllWindows()
                    process_image(self.camera_index, self.model_path)
                    return

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    cap.release()
                    cv2.destroyAllWindows()
                    return

if __name__ == "__main__":
    steps_data = load_steps_data()
    camera_data = load_camera_data()
    global_steps = populate_global_steps(steps_data)
    model_path = "best.pt"

    # Create queues for communication
    person_queue = multiprocessing.Queue()
    yolo_queue = multiprocessing.Queue()
    result_queue = multiprocessing.Queue()

    # Start queue processing
    queue_process = multiprocessing.Process(target=process_queues, args=(global_steps, person_queue, yolo_queue, result_queue))
    queue_process.start()

    root = tk.Tk()
    app = StepTrackingApp(root, global_steps, camera_data, model_path)

    def update_gui():
        if not result_queue.empty():
            step = result_queue.get()
            app.completed_steps.append(step)
            app.update_highlight()

            if len(app.completed_steps) == len(global_steps):
                app.mark_complete()

        root.after(100, update_gui)

    root.after(100, update_gui)
    root.mainloop()

    queue_process.terminate()
