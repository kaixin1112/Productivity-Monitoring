from flask import Flask, render_template, request, redirect, url_for, Response
from datetime import datetime
import cv2
import os
import webbrowser
from threading import Timer
import numpy as np
import time

#from Person_Det import CONFIG_PATH
#from Person_Det import LABELS_PATH

app = Flask(__name__)

# Enable auto-reloading of templates
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Hardcoded credentials for demonstration
STAFF_CREDENTIALS = {
    "admin": "password123",
    "user1": "mypassword",
    "flex1": "flex1pass"
}

#camera = cv2.VideoCapture(0)  # Initialize camera

# Path to the model files
FROZEN_GRAPH_PATH = "frozen_inference_graph.pb"
CONFIG_PATH = "ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt"
LABELS_PATH = "coco.names"

# Validate paths
if not os.path.exists(FROZEN_GRAPH_PATH):
    raise FileNotFoundError(f"Model file not found: {FROZEN_GRAPH_PATH}")
if not os.path.exists(CONFIG_PATH):
    raise FileNotFoundError(f"Config file not found: {CONFIG_PATH}")
if not os.path.exists(LABELS_PATH):
    raise FileNotFoundError(f"Labels file not found: {LABELS_PATH}")


# Load class labels
def load_labels(label_path):
   with open(label_path, 'r') as file:
       labels = {i: line.strip() for i, line in enumerate(file.readlines())}
   return labels

labels = load_labels(LABELS_PATH)

# Load the model 
net = cv2.dnn_DetectionModel(FROZEN_GRAPH_PATH, CONFIG_PATH)
net.setInputSize(300, 300)
net.setInputScale(1.0 / 127.5)
net.setInputMean((127.5, 127.5, 127.5))
net.setInputSwapRB(True)

@app.route('/')
def index():
    #print("Index route called")
    #return render_template('index.html')  # Renders the welcome page
    return redirect(url_for('login')) # Automatically redirect to the login page

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        staff_id = request.form['staff_id']
        password = request.form['password']
        if staff_id in STAFF_CREDENTIALS and STAFF_CREDENTIALS[staff_id] == password:
            return redirect(url_for('dashboard'))
        else:
            return "Invalid Staff ID or Password", 403
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    #from datetime import datetime
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S') # Format the current time
    return render_template('dashboard.html', time=current_time) # Pass time to the template

@app.route('/productivity')
def productivity():
    return render_template('productivity.html')

@app.route('/logout')
def logout():
    return redirect(url_for('login'))

@app.route('/video_feed_laptop')
def video_feed_external():
    # Route for the laptop camera
    return Response(generate_person_detection_frames(camera_id=0), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed_webcam')
def video_feed_webcam():
    # Route for the webcam
    return Response(generate_standard_frames(camera_id=1), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed_epoccam')
def video_feed_epoccam():
    return Response(generate_standard_frames(camera_id=2), mimetype='multipart/x-mixed-replace; boundary=frame')

def generate_person_detection_frames(camera_id=0):
    try:
       camera = cv2.VideoCapture(camera_id)
       if not camera.isOpened():
        print(f"Camera {camera_id} is not available, showing black frame.")
        #raise RuntimeError(f"Could not open camera {camera_id}")

        while True:
          black_frame = np.zeros((480, 640, 3), dtype=np.uint8) # Black frame with 480p resolution
          _, buffer = cv2.imencode('.jpg', black_frame)
          frame = buffer.tobytes()
          yield (b'--frame\r\n'
                 b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        
       while True:
            success, frame = camera.read()
            if not success or frame is None:
              print(f"Invalid frame from camera {camera_id}, skipping...")
              continue

            frame = cv2.resize(frame, (640, 480))

            # Detect objects in the frame
            class_ids, confidences, boxes = net.detect(frame, confThreshold=0.6) 

            # Draw bounding boxes and labels
            for class_id, confidence, box in zip(class_ids.flatten(), confidences.flatten(), boxes):
                if class_id == 1:  # Class ID 1 corresponds to "person"
                    label = f"{labels[class_id]}: {confidence:.2f}"
                    x, y, w, h = box
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Encode the frame for display
            if frame is not None and isinstance(frame, np.ndarray):
                _, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  
            else:
                print("Skipped encoding invalid frame.")
                time.sleep(0.03) 
    except Exception as e:
         print(f"Error with camera {camera_id}: {e}")
    finally:
         if 'camera' in locals() and camera.isOpened():
             camera.release()

def generate_standard_frames(camera_id=0):
    try:
        camera = cv2.VideoCapture(camera_id)
        if not camera.isOpened():
            print(f"Camera {camera_id} is not available.")
            while True:
                black_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                _, buffer = cv2.imencode('.jpg', black_frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        while True:
            success, frame = camera.read()
            if not success:
                break

            _, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    except Exception as e:
        print(f"Error with camera {camera_id}: {e}")
    finally:
        if 'camera' in locals() and camera.isOpened():
            camera.release()
                   


# Open browser automatically after server starts
def open_browser():
    webbrowser.open_new("http://127.0.0.1:2102")

#print("Before starting Flask app")
if __name__ == '__main__':
      # Debug: Check avalibale cameras
      print("Checking available cameras...")
      index = 0
      while True:
          cap = cv2.VideoCapture(index)
          if not cap.read()[0]:
              break
          else:
              print(f"Camera {index} is available.")
          cap.release()
          index += 1
      Timer(1, open_browser).start() # Open the browser after 1 second
      print("Starting Flask server...")
      app.run(debug=True, port=2102)
      print("Flask server started")