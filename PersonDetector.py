import cv2
import os

class PersonDetector:
    def __init__(self):
        # Load class labels
        with open("coco.names", "r") as file:
            self.class_names = [line.strip() for line in file.readlines()]
        self.person_class_id = self.class_names.index("person")  # Get the class ID for 'person'

        self.model_path = "frozen_inference_graph.pb"
        self.config_path = "ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt"

        # Load pre-trained DNN model
        self.net = cv2.dnn_DetectionModel(self.model_path, self.config_path)
        self.net.setInputSize(320, 320)
        self.net.setInputScale(1.0 / 127.5)
        self.net.setInputMean((127.5, 127.5, 127.5))
        self.net.setInputSwapRB(True)

    def detect_persons(self, frame, rois):
        detections = self.net.detect(frame, confThreshold=0.7)  # Confidence threshold set to 0.7
        class_ids, confidences, boxes = detections if len(detections) == 3 else ([], [], [])

        global_cam = []  # Store detections within specific ROIs

        if len(class_ids) > 0:
            for i, (class_id, confidence, box) in enumerate(zip(class_ids.flatten(), confidences.flatten(), boxes)):
                if class_id == self.person_class_id:
                    if i == 0:  # Only consider the first detected person
                        x, y, w, h = box
                        center_x = x + w // 2
                        center_y = y + h // 2
                        for idx, (rx, ry, rw, rh) in enumerate(rois):
                            # Check if the detection is within a specific ROI
                            if rx <= center_x <= rx + rw and ry <= center_y <= ry + rh:
                                global_cam.append((idx + 1, "Person"))

                        # Draw bounding box and label on the frame
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 2)
                        cv2.putText(frame, "Person", (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                    else:
                        break  # Ignore additional detections
        return frame, global_cam

    def draw_rois(self, frame, rois):
        for idx, roi in enumerate(rois):
            x, y, w, h = roi
            top_left = (x, y)
            bottom_right = (x + w, y + h)

            # Draw green rectangle
            cv2.rectangle(frame, top_left, bottom_right, color=(0, 255, 0), thickness=2)

            # Add label
            label = f"ROI {idx + 1}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            lbl_w, lbl_h = label_size[0]
            lbl_margin = 3
            lbl_x = x
            lbl_y = y - lbl_h - lbl_margin

            # Draw green background for text
            cv2.rectangle(frame, (lbl_x, lbl_y), 
                        (lbl_x + lbl_w + 2 * lbl_margin, lbl_y + lbl_h + 2 * lbl_margin), 
                        color=(0, 255, 0), thickness=-1)

            # Draw text in black
            cv2.putText(frame, label, (lbl_x + lbl_margin, lbl_y + lbl_h), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

        return frame


    def run(self, camera_index):
        cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)

        def load_roi_data(camera_id):
            roi_file = f"ROI_CAM_{camera_id}.txt"
            if os.path.exists(roi_file):
                with open(roi_file, "r") as file:
                    roi_data = eval(file.read().split("=")[1].strip())
                return roi_data
            return []

        if not cap.isOpened():
            print(f"Error: Unable to open camera with index {camera_index}")
            return

        rois = load_roi_data(camera_index)  # Load ROIs once

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Error: Unable to read frame from camera")
                    break

                # Draw ROIs on the frame
                frame = self.draw_rois(frame, rois)

                # Detect persons in the frame
                frame, global_cam = self.detect_persons(frame, rois)

                # Display the frame
                cv2.imshow("Person Detection with ROIs", frame)

                # Exit loop on 'q' key press
                if cv2.waitKey(1) & 0xFF == ord('q') or cv2.getWindowProperty('Person Detection with ROIs', cv2.WND_PROP_VISIBLE) < 1:
                    break

        finally:
            cap.release()
            cv2.destroyAllWindows()

if __name__ == '__main__':
    detector = PersonDetector()
    detector.run(0)