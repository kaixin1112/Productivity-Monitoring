from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse, RedirectResponse, HTMLResponse
import cv2
import json
import time
import platform

CAMERA_DATA_PATH = "camera_data.json"  # Path to the JSON file with camera data

# Load the class labels
def load_labels(label_path):
    with open(label_path, 'r') as file:
        labels = {i: line.strip() for i, line in enumerate(file.readlines())}
    return labels

# Load camera data from JSON
def load_camera_data(json_path):
    try:
        with open(json_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"{json_path} not found.")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON in {json_path}.")

# Initialize FastAPI
app = FastAPI()

# Person Detection Class
class PersonDetector:
    def __init__(self, model_path, config_path, label_map):
        self.net = cv2.dnn_DetectionModel(model_path, config_path)
        self.net.setInputSize(320, 320)
        self.net.setInputScale(1.0 / 127.5)
        self.net.setInputMean((127.5, 127.5, 127.5))
        self.net.setInputSwapRB(True)
        self.labels = label_map

    def detect_and_annotate(self, frame):
        detections = self.net.detect(frame, confThreshold=0.5)
        if detections is None or len(detections) != 3:
            class_ids, confidences, boxes = [], [], []
        else:
            class_ids, confidences, boxes = detections

        for class_id, confidence, box in zip(class_ids.flatten(), confidences.flatten(), boxes):
            if class_id == 1 and confidence > 0.7:  # Class ID 1 corresponds to "person"
                label = f"{self.labels[class_id]}: {confidence:.2f}"
                x, y, w, h = box
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        return frame


def generate_frames(camera_id, apply_detection=False):
    # Platform-independent camera access
    if platform.system() != "Windows":
        camera = cv2.VideoCapture(int(camera_id))  # No CAP_DSHOW for non-Windows
    else:
        camera = cv2.VideoCapture(int(camera_id), cv2.CAP_DSHOW)
    
    fps = 0
    while True:
        start_time = cv2.getTickCount()  # Start timer
        success, frame = camera.read()
        if not success:
            break

        # Calculate FPS
        end_time = cv2.getTickCount()
        time_taken = (end_time - start_time) / cv2.getTickFrequency()
        fps = 1 / time_taken if time_taken > 0 else 0

        # Display FPS on frame
        height, width, _ = frame.shape
        position = (10, height - 10)  # Adjust to place FPS at the bottom left
        fps_label = f"FPS: {fps:.0f}"
        cv2.putText(frame, fps_label, position, cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Encode frame as JPEG
        _, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
    camera.release()


@app.get("/")
def redirect_to_video_feed():
    return RedirectResponse(url="/multi_camera_view")


@app.get("/video_feed")
def video_feed(
    camera_id: str = Query("0", description="Camera ID from the configuration"),
    apply_detection: bool = Query(False, description="Enable person detection")
):
    """
    Stream the video feed.
    :param camera_id: ID of the camera to use (from JSON configuration)
    :param apply_detection: Enable or disable person detection
    """
    try:
        int(camera_id)  # Validate camera_id is an integer
    except ValueError:
        return {"error": "Invalid camera_id. Must be an integer."}
    
    return StreamingResponse(
        generate_frames(camera_id, apply_detection=apply_detection),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@app.get("/cameras")
def list_cameras():
    """
    List all available cameras by dynamically reading the camera_data.json file.
    """
    try:
        camera_data = load_camera_data(CAMERA_DATA_PATH)  # Dynamically reload the JSON file
        return {"cameras": camera_data}
    except Exception as e:
        return {"error": f"Failed to load camera data: {str(e)}"}
    

@app.get("/multi_camera_view", response_class=HTMLResponse)
def multi_camera_view():
    """
    Serve an HTML page that displays video feeds from all cameras in the JSON file.
    """
    camera_data = load_camera_data(CAMERA_DATA_PATH)
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Multi-Camera View</title>
        <style>
            body {
                display: flex;
                flex-wrap: wrap;
                justify-content: center;
                align-items: center;
                margin: 0;
                padding: 0;
                background-color: #f4f4f4;
            }
            .camera-feed {
                margin: 10px;
                border: 2px solid #ccc;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                width: 45%; /* Adjust size as needed */
            }
            iframe {
                width: 100%;
                height: 400px; /* Adjust size as needed */
                border: none;
                overflow: hidden; /* Prevent scrollbars */
                scrolling: no; /* Ensure no scrollbars are displayed */
            }
        </style>
    </head>
    <body>
    """
    for camera_id, camera_info in camera_data.items():
        if 'Camera ID' in camera_info and 'Technique' in camera_info:
            html_content += f"""
            <div class="camera-feed">
                <h3>Camera: {camera_info['Camera ID']} - {camera_info['Technique']}</h3>
                <iframe src="/video_feed?camera_id={camera_info['Camera ID']}&apply_detection=false" frameborder="0" scrolling="no"></iframe>
            </div>
            """
    html_content += """
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
