import cv2
import os
import mediapipe as mp
import torch
from udp_send import udp_sender

class PersonDetector:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.person_detected_last_frame = False  # State to track person detection

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

    def detect_and_draw_skeleton(self, frame, rois, queue, camera_index):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(rgb_frame)

        person_detected = False

        if results.pose_landmarks:
            # Get coordinates for eyes and nose
            landmarks = results.pose_landmarks.landmark
            left_eye = landmarks[self.mp_pose.PoseLandmark.LEFT_EYE]
            right_eye = landmarks[self.mp_pose.PoseLandmark.RIGHT_EYE]
            nose = landmarks[self.mp_pose.PoseLandmark.NOSE]

            if left_eye.visibility > 0.5 and right_eye.visibility > 0.5 and nose.visibility > 0.5:
                le_x, le_y = int(left_eye.x * frame.shape[1]), int(left_eye.y * frame.shape[0])
                re_x, re_y = int(right_eye.x * frame.shape[1]), int(right_eye.y * frame.shape[0])
                nose_x, nose_y = int(nose.x * frame.shape[1]), int(nose.y * frame.shape[0])

                for idx, (rx1, ry1, rw, rh) in enumerate(rois):
                    # Check if both eyes and nose are inside the ROI
                    in_roi = (rx1 <= le_x <= rx1 + rw and ry1 <= le_y <= ry1 + rh and
                              rx1 <= re_x <= rx1 + rw and ry1 <= re_y <= ry1 + rh and
                              rx1 <= nose_x <= rx1 + rw and ry1 <= nose_y <= ry1 + rh)
                    if in_roi:
                        queue.put({"camera_index": camera_index, "roi": idx + 1, "object": "Person"})

                person_detected = True

            # Draw skeleton on the frame
            mp.solutions.drawing_utils.draw_landmarks(
                frame, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS,
                mp.solutions.drawing_utils.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                mp.solutions.drawing_utils.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=2)
            )

        # Annotate frame based on detection status
        if person_detected:
            cv2.putText(frame, "Person Detected", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            self.person_detected_last_frame = True  # Update the state
            udp_sender("192.168.43.58", 12345, 'Stop')
        else:
            cv2.putText(frame, "Person Not Present", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            # Only send UDP alert if no person was detected in the current frame
            # and a person was detected in the previous frame
            if self.person_detected_last_frame:
                self.person_detected_last_frame = False  # Reset state
                udp_sender("192.168.43.58", 12345, 'Alert')

        return frame

    def run(self, camera_index, queue):
        cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)

        if not cap.isOpened():
            print(f"Error: Unable to open camera with index {camera_index}")
            return

        # Load Region of Interest (ROI) data from a file
        def load_roi_data(camera_id):
            roi_file = f"ROI_CAM_{camera_id}.txt"
            if os.path.exists(roi_file):
                with open(roi_file, "r") as file:
                    roi_data = eval(file.read().split("=")[1].strip())
                return roi_data
            return []

        rois = load_roi_data(camera_index)  # Load ROIs once

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Error: Unable to read frame from camera")
                    break

                # Draw ROIs on the frame
                frame = self.draw_rois(frame, rois)

                # Detect persons and draw skeletons
                frame = self.detect_and_draw_skeleton(frame, rois, queue, camera_index)

                # Display the frame
                cv2.imshow("Person Detection with Skeleton", frame)

                # Empty GPU memory
                torch.cuda.empty_cache()

                # Exit loop on 'q' key press
                if cv2.waitKey(1) & 0xFF == ord('q') or cv2.getWindowProperty('Person Detection with Skeleton', cv2.WND_PROP_VISIBLE) < 1:
                    break
        finally:
            cap.release()
            cv2.destroyAllWindows()

if __name__ == '__main__':
    from queue import Queue

    detection_queue = Queue()
    detector = PersonDetector()
    detector.run(1, detection_queue)
