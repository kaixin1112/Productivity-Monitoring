import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import multiprocessing
from multiprocessing import Event
from ultralytics import YOLO
import cv2
import json
from YOLODetector import YOLODetector
from PersonDetector import PersonDetector
import numpy as np
import time
import tkinter.font as tkFont
from upload_to_dropbox import DropboxUploader

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

def run_person_detector(camera_index, queue, terminate_flag):
    """Standalone function for Person Detection."""
    detector = PersonDetector()
    detector.run(camera_index, queue)

def run_yolo_detector(model_path, camera_index, queue, terminate_flag):
    """Standalone function for YOLO Detection."""
    detector = YOLODetector(model_path)
    detector.run(camera_index=camera_index, threshold=0.6, queue=queue, terminate_flag=terminate_flag)

def process_queues(global_steps, person_queue, yolo_queue, result_queue, terminate_flag):
    """Processes queues to validate detections and handle step completions."""
    current_step = 1
    false_object_detected = False  # Tracks if a false object is currently detected

    while current_step <= len(global_steps) and not terminate_flag.is_set():
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

        # Handle empty YOLO object case
        if yolo_message:
            # False object detected in ROI
            if (yolo_message["camera_index"] == expected_camera_index and
                yolo_message["roi"] == expected_roi and
                yolo_message["object"] != "" and
                yolo_message["object"] != expected_object):

                if not false_object_detected:  # Only send message once
                    result_queue.put({
                        "status": False,
                        "message": f"{expected_object} should be in ROI {expected_roi}"
                    })
                    false_object_detected = True  # Mark false object as detected
                continue

            # False object has left the ROI
            elif (yolo_message["camera_index"] == expected_camera_index and
                yolo_message["roi"] == expected_roi and
                yolo_message["object"] == None):
                false_object_detected = False  # Reset false object detection
                result_queue.put({
                    "status": True,
                    "message": ""  # Send an empty message to clear the error
                })
                continue

            # Correct object detected
            elif (yolo_message["camera_index"] == expected_camera_index and
                  yolo_message["roi"] == expected_roi and
                  yolo_message["object"] == expected_object):
                result_queue.put(current_step)
                current_step += 1
                false_object_detected = False  # Reset false object detection
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

def process_image(frame, model_path):
    """Process frame and display results."""
    detections = analyze_photo(frame, model_path)

    # Initialize the uploader
    uploader = DropboxUploader(token_file="dropbox_tokens.json")

    # Draw bounding boxes
    for detection in detections:
        x1, y1, x2, y2 = detection["bbox"]
        label = detection["label"]
        confidence = detection["confidence"]
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, f"{label}: {confidence:.2f}", (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Check components
    required_components = {"Motor": 2, "Wheel": 2, "Driver": 1, "ESP32": 1}
    for detection in detections:
        label = detection["label"]
        if label in required_components and required_components[label] > 0:
            required_components[label] -= 1

    # Determine pass/fail
    if all(count == 0 for count in required_components.values()):
        cv2.putText(frame, "PASS", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("Capture Result", frame)
        cv2.waitKey(1)

        # Prompt for Barcode ID
        root = tk.Tk()
        root.withdraw()
        barcode_id = simpledialog.askstring("Input", "Enter Barcode ID:")

        if barcode_id:
            timestamp = time.strftime("%d%m%Y-%H%M%S")
            filename = f"{barcode_id}_{timestamp}.png"
            # Save the image with the barcode and timestamp
            cv2.imwrite(filename, frame)
            # Upload the file to Dropbox
            uploader.upload_single_file(filename)
        else:
            print("No Barcode ID entered.")

        return "PASS"
    else:
        missing_items = [item for item, count in required_components.items() if count > 0]
        missing_message = f"Item Missing: {', '.join(missing_items)}"
        cv2.putText(frame, "FAIL", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.imshow("Capture Result", frame)
        cv2.waitKey(1)

        # Show error message
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Error", missing_message)
        print(missing_message)

        return "FAIL"

class StepTrackingApp:
    def __init__(self, root, global_steps, camera_data, model_path):
        self.root = root
        self.global_steps = global_steps
        self.camera_data = camera_data
        self.model_path = model_path
        self.completed_steps = []
        self.time_elapsed = 0  # Timer starts at 0 seconds

        # Configure the window
        self.root.title("Step Tracking")

        # Define a larger font
        self.custom_font = tkFont.Font(family="Helvetica", size=13)
        self.header_font = tkFont.Font(family="Helvetica", size=15, weight="bold")

        # Configure the Treeview style
        style = ttk.Style()
        style.configure("Treeview", font=self.custom_font, rowheight=25)  # Font for the rows
        style.configure("Treeview.Heading", font=self.header_font)  # Font for the headers

        self.table = ttk.Treeview(root, columns=("Camera Index", "ROI", "Object"), show="headings")
        self.table.heading("Camera Index", text="Camera Index")
        self.table.heading("ROI", text="ROI")
        self.table.heading("Object", text="Object")
        self.table.pack(fill=tk.BOTH, expand=True)

        # Populate the table with global_steps
        for idx, (step, data) in enumerate(global_steps.items(), start=1):
            self.table.insert("", "end", iid=step, values=(data[0], data[1], data[2]))

        self.message_box = tk.Label(root, text="", fg="red", wraplength=400, justify="left", font=self.custom_font)
        self.message_box.pack(pady=10)

        # Timer and Target Section
        timer_frame = tk.Frame(root)
        timer_frame.pack(fill=tk.X, pady=5)
        tk.Label(timer_frame, text="Timer:").grid(row=0, column=0)
        self.timer_label = tk.Label(timer_frame, text="00:00")
        self.timer_label.grid(row=0, column=1)

        # Create terminate flag
        self.terminate_flag = Event()

        self.update_timer()

        # Start camera processes
        self.start_camera_processes()

    def start_camera_processes(self):
        for cam_id, cam_info in self.camera_data.items():
            camera_index = int(cam_info["Camera ID"])
            technique = cam_info["Technique"]

            if technique == "Person Detection":
                process = multiprocessing.Process(target=run_person_detector, args=(camera_index, person_queue, self.terminate_flag))
                process.start()
            elif technique == "Object Detection (Vid)":
                process = multiprocessing.Process(target=run_yolo_detector, args=(self.model_path, camera_index, yolo_queue, self.terminate_flag))
                process.start()

    def update_timer(self):
        """Update the timer every second to show elapsed time in minutes and seconds."""
        self.time_elapsed += 1
        minutes = self.time_elapsed // 60
        seconds = self.time_elapsed % 60
        self.timer_label["text"] = f"{minutes:02}:{seconds:02}"
        self.root.after(1000, self.update_timer)

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

        # Terminate background processes
        self.terminate_flag.set()

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
        """Open OpenCV window for capture."""
        cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        if not cap.isOpened():
            print("Error: Unable to access camera.")
            return

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Error: Unable to read from camera.")
                    break

                cv2.imshow("Live Feed - Press 'c' to Capture or 'q' to Quit", frame)

                key = cv2.waitKey(1) & 0xFF
                if key == ord('c'):
                    process_result = process_image(frame, self.model_path)

                    if process_result == "PASS":
                        return

                    elif process_result == "FAIL":
                        # Continue streaming until a valid capture is made
                        continue

                elif key == ord('q'):
                    break
        finally:
            cap.release()
            cv2.destroyAllWindows()

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
    terminate_flag = Event()
    queue_process = multiprocessing.Process(target=process_queues, args=(global_steps, person_queue, yolo_queue, result_queue, terminate_flag))
    queue_process.start()

    root = tk.Tk()
    app = StepTrackingApp(root, global_steps, camera_data, model_path)

    def update_gui():
        if not result_queue.empty():
            result = result_queue.get()

            if isinstance(result, int):  # Step completed
                app.completed_steps.append(result)
                app.update_highlight()
                app.message_box.config(text="")  # Clear the message box

                if len(app.completed_steps) == len(global_steps):
                    app.mark_complete()

            elif isinstance(result, dict):
                if not result["status"]:  # False condition
                    # Update the message box with the error message
                    app.message_box.config(text=result["message"])
                elif result["status"]:  # Clear message on valid condition
                    app.message_box.config(text="")

        root.after(100, update_gui)

    root.after(100, update_gui)
    root.mainloop()

    terminate_flag.set()
    queue_process.join()
