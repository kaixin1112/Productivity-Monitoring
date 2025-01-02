import cv2
import numpy as np
from ultralytics import YOLO
import torch

class YOLODetector:
    def __init__(self, model_path):
        self.model = YOLO(model_path)  # Load your custom model
        self.model.fuse()

    def plot_bboxes(self, results, threshold=0.5):
        img = results[0].orig_img  # original image
        names = results[0].names  # class names dict
        scores = results[0].boxes.conf.cpu().numpy()  # probabilities (moved to CPU)
        classes = results[0].boxes.cls.cpu().numpy()  # predicted classes (moved to CPU)
        boxes = results[0].boxes.xyxy.cpu().numpy().astype(np.int32)  # bboxes (moved to CPU)
        for score, cls, bbox in zip(scores, classes, boxes):  # loop over all bboxes
            if score >= threshold:  # Apply confidence threshold
                class_label = names[int(cls)]  # class name
                label = f"{class_label} : {score:0.2f}"  # bbox label
                lbl_margin = 2  # label margin
                img = cv2.rectangle(img, (bbox[0], bbox[1]),
                                    (bbox[2], bbox[3]),
                                    color=(255, 0, 0),  # blue color for bounding box
                                    thickness=1)
                label_size = cv2.getTextSize(label,  # label size in pixels
                                            fontFace=cv2.FONT_HERSHEY_SIMPLEX, 
                                            fontScale=0.5, thickness=1)  # smaller font scale
                lbl_w, lbl_h = label_size[0]  # label w and h
                lbl_w += 2 * lbl_margin  # add margins on both sides
                lbl_h += 2 * lbl_margin
                img = cv2.rectangle(img, (bbox[0], bbox[1]),  # plot label background
                                    (bbox[0] + lbl_w, bbox[1] - lbl_h),
                                    color=(255, 0, 0),  # blue color for label background
                                    thickness=-1)  # thickness=-1 means filled rectangle
                cv2.putText(img, label, (bbox[0] + lbl_margin, bbox[1] - lbl_margin),  # write label to the image
                            fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                            fontScale=0.5, color=(255, 255, 255),  # smaller text in white
                            thickness=1)
        return img

    def load_rois(self, camera_index):
        roi_file = f"ROI_CAM_{camera_index}.txt"
        rois = []
        try:
            with open(roi_file, "r") as file:
                content = file.read()
                rois = eval(content.split("=")[1].strip())  # Convert the string list to Python list
        except Exception as e:
            print(f"Error reading ROIs: {e}")
        return rois

    def draw_rois(self, frame, rois):
        for idx, roi in enumerate(rois):
            x, y, w, h = roi
            top_left = (x, y)
            bottom_right = (x + w, y + h)

            # Draw the green rectangle for the ROI
            cv2.rectangle(frame, top_left, bottom_right, color=(0, 255, 0), thickness=2)

            # Prepare the label
            label = f"ROI {idx + 1}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            lbl_w, lbl_h = label_size[0]
            lbl_margin = 3
            lbl_x = x
            lbl_y = y - lbl_h - lbl_margin

            # Draw green background for the label
            cv2.rectangle(frame, (lbl_x, lbl_y),
                        (lbl_x + lbl_w + 2 * lbl_margin, lbl_y + lbl_h + 2 * lbl_margin),
                        color=(0, 255, 0), thickness=-1)

            # Add label text in black
            cv2.putText(frame, label, (lbl_x + lbl_margin, lbl_y + lbl_h),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

        return frame

    def run(self, camera_index=0, threshold=0.5, queue=None):
        cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)

        if not cap.isOpened():
            print("Error: Unable to open camera.")
            return

        rois = self.load_rois(camera_index)

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Error: Unable to read frame.")
                    break

                # Draw ROIs on the frame
                frame = self.draw_rois(frame, rois)

                # Perform detection
                results = self.model(frame, verbose=False)
                names = results[0].names
                scores = results[0].boxes.conf.cpu().numpy()
                classes = results[0].boxes.cls.cpu().numpy().astype(int)
                boxes = results[0].boxes.xyxy.cpu().numpy().astype(np.int32)

                roi_detections = {i + 1: [] for i in range(len(rois))}

                for score, cls, box in zip(scores, classes, boxes):
                    if score >= threshold:
                        x1, y1, x2, y2 = box
                        center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2
                        obj = names[cls]

                        # Draw bounding box for detected object
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color=(255, 0, 0), thickness=2)
                        label = f"{obj}: {score:.2f}"
                        cv2.putText(frame, label, (x1, y1 - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

                        for idx, (rx, ry, rw, rh) in enumerate(rois):
                            if rx <= center_x <= rx + rw and ry <= center_y <= ry + rh:
                                roi_detections[idx + 1].append(obj)
                                break

                # Sort and send detections
                for roi_index, detected_objects in roi_detections.items():
                    if detected_objects:
                        detected_objects.sort()
                        queue.put({
                            "camera_index": camera_index,
                            "roi": roi_index,
                            "object": detected_objects
                        })

                # Display the frame
                cv2.imshow("YOLO Detection with ROIs and Bounding Boxes", frame)

                # Empty GPU memory
                torch.cuda.empty_cache()

                if cv2.waitKey(1) & 0xFF == ord('q') or cv2.getWindowProperty('YOLO Detection with ROIs and Bounding Boxes', cv2.WND_PROP_VISIBLE) < 1:
                    break
        finally:
            cap.release()
            cv2.destroyAllWindows()

if __name__ == '__main__':
    detector = YOLODetector('best.pt')
    detector.run(camera_index=1, threshold=0.7)