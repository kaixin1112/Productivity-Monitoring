import cv2
import mediapipe as mp
import math
from time import time

# Initialize MediaPipe Pose with simplified model complexity for better FPS
mp_pose = mp.solutions.pose
pose_video = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5, model_complexity=0)
mp_drawing = mp.solutions.drawing_utils

def calculate_angle(point1, point2, point3):
    """
    Calculate the angle between three points.
    Args:
        point1, point2, point3: (x, y, z) coordinates of three points.
    Returns:
        angle: Angle in degrees between the three points. Returns 0 if points are invalid.
    """
    if any(p == (0, 0, 0) for p in [point1, point2, point3]):
        return 0  # Invalid point

    x1, y1, _ = point1
    x2, y2, _ = point2
    x3, y3, _ = point3

    # Calculate the vectors
    v1 = (x1 - x2, y1 - y2)
    v2 = (x3 - x2, y3 - y2)

    # Calculate the angle
    angle = math.degrees(math.atan2(v2[1], v2[0]) - math.atan2(v1[1], v1[0]))
    angle = abs(angle)  # Convert to positive
    if angle > 180.0:
        angle = 360 - angle
    return angle

def detectPose(image, pose, display=True):
    '''
    Detects and displays pose landmarks on an image.
    Args:
        image: The input image to process.
        pose: The MediaPipe pose model used for detection.
        display: If True, shows the original and annotated images with a 3D plot of landmarks.
    Returns:
        output_image: The image with drawn pose landmarks (if display is False).
        landmarks: A list of (x, y, z) coordinates of detected landmarks (if display is False).
    '''
    output_image = image.copy()
    imageRGB = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = pose.process(imageRGB)

    height, width, _ = image.shape
    landmarks = []

    if results.pose_landmarks:
        # Only add landmarks with sufficient visibility
        for landmark in results.pose_landmarks.landmark:
            if landmark.visibility > 0.5:
                landmarks.append((int(landmark.x * width), int(landmark.y * height), int(landmark.z * width)))
            else:
                landmarks.append((0, 0, 0))  # Invalid landmark

    return output_image, landmarks

# Initialize Video Capture
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cv2.namedWindow('Pose Detection', cv2.WINDOW_NORMAL)
cap.set(3, 640)
cap.set(4, 480)

time1 = 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame_height, frame_width, _ = frame.shape
    frame = cv2.resize(frame, (int(frame_width * (640 / frame_height)), 640))

    # Perform Pose Landmark Detection
    frame, landmarks = detectPose(frame, pose_video, display=False)

    # Check if both elbows are detected and visible
    if landmarks:
        try:
            # Define keypoints for elbows
            left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            left_elbow = landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value]
            left_wrist = landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value]

            right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
            right_elbow = landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value]
            right_wrist = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value]

            # Calculate angles for both elbows
            left_elbow_angle = calculate_angle(left_shoulder, left_elbow, left_wrist)
            right_elbow_angle = calculate_angle(right_shoulder, right_elbow, right_wrist)

            status = None
            color = (0, 0, 255)  # Default to red (Not Working)

            # Only display status if both elbows are valid
            if left_elbow_angle > 0 and right_elbow_angle > 0:
                # If angles indicate "Working" position
                if (160 >= left_elbow_angle) or (160 >= right_elbow_angle):
                    status = "Working"
                    color = (0, 255, 0)  # Green for working
                else:
                    status = "Not Working"

            # Display status on the frame
            if status:
                cv2.putText(frame, status, (frame_width - 200, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

        except IndexError:
            pass

    # Calculate and display FPS
    time2 = time()
    if (time2 - time1) > 0:
        frames_per_second = 1.0 / (time2 - time1)
        cv2.putText(frame, f'FPS: {int(frames_per_second)}', (10, 30), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 3)

    time1 = time2

    # Display the frame
    cv2.imshow('Pose Detection', frame)

    # Wait until 'ESC' key is pressed
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
