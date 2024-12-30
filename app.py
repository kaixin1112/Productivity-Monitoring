import os
import cv2
import time
import socket
import numpy as np
from flask import Flask, render_template, request, redirect, url_for, Response
from threading import Timer
from datetime import datetime
import webbrowser

class ProductivityApp:
    def __init__(self, host="127.0.0.1", port=2102):
        self.app = Flask(__name__)
        self.host = host
        self.port = port
        self.staff_credentials = {
            "admin": "password123",
            "user1": "mypassword",
            "flex1": "flex1pass"
        }

        # Paths to the model files
        self.frozen_graph_path = "frozen_inference_graph.pb"
        self.config_path = "ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt"
        self.labels_path = "coco.names"

        self.labels = self.load_labels(self.labels_path)
        self.net = self.load_model()

        # Define Flask routes
        self.define_routes()

    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception as e:
            print(f"Error getting local IP: {e}")
            return "127.0.0.1"

    def load_labels(self, label_path):
        if not os.path.exists(label_path):
            raise FileNotFoundError(f"Labels file not found: {label_path}")
        with open(label_path, 'r') as file:
            labels = {i: line.strip() for i, line in enumerate(file.readlines())}
        return labels

    def load_model(self):
        if not os.path.exists(self.frozen_graph_path):
            raise FileNotFoundError(f"Model file not found: {self.frozen_graph_path}")
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        net = cv2.dnn_DetectionModel(self.frozen_graph_path, self.config_path)
        net.setInputSize(300, 300)
        net.setInputScale(1.0 / 127.5)
        net.setInputMean((127.5, 127.5, 127.5))
        net.setInputSwapRB(True)
        return net

    def define_routes(self):
        @self.app.route('/')
        def index():
            return redirect(url_for('login'))

        @self.app.route('/login', methods=['GET', 'POST'])
        def login():
            if request.method == 'POST':
                staff_id = request.form['staff_id']
                password = request.form['password']
                if staff_id in self.staff_credentials and self.staff_credentials[staff_id] == password:
                    return redirect(url_for('dashboard'))
                else:
                    return "Invalid Staff ID or Password", 403
            return render_template('login.html')

        @self.app.route('/dashboard')
        def dashboard():
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            return render_template('dashboard.html', time=current_time)

        @self.app.route('/productivity')
        def productivity():
            return render_template('productivity.html')

        @self.app.route('/logout')
        def logout():
            return redirect(url_for('login'))

        @self.app.route('/video_feed_laptop')
        def video_feed_external():
            return Response(self.generate_frames(camera_id=0), mimetype='multipart/x-mixed-replace; boundary=frame')

        @self.app.route('/video_feed_webcam')
        def video_feed_webcam():
            return Response(self.generate_frames(camera_id=1), mimetype='multipart/x-mixed-replace; boundary=frame')

        @self.app.route('/video_feed_epoccam')
        def video_feed_epoccam():
            return Response(self.generate_frames(camera_id=2), mimetype='multipart/x-mixed-replace; boundary=frame')
        
        @self.app.route("/steps")
        def steps():
            return render_template('steps.html')

    global cameras
    # Initialize global cameras at the start of the app
    cameras = {0: cv2.VideoCapture(0), 1: cv2.VideoCapture(1), 2: cv2.VideoCapture(2)}

    def generate_frames(self, camera_id):
        camera = cameras.get(camera_id)
        while True:
            success, frame = camera.read()
            if not success:
                break
            _, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    def open_browser(self):
        """Automatically open the browser when the app starts."""
        url = f"http://{self.host}:{self.port}"
        webbrowser.open_new(url)

    def run(self, **kwargs):
        """Run the app and open the browser after a brief delay."""
        print(f"Starting app on http://{self.host}:{self.port}")
        # Use a Timer to open the browser 1 second after the app starts
        Timer(1, self.open_browser).start()
        self.app.run(debug=True, host=self.host, port=self.port, **kwargs)
