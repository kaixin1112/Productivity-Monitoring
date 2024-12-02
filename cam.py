import cv2
import os, ast

class CAM_ROI:
    def __init__(self, index):
        self.index = index
        # Initialize camera
        self.cap = cv2.VideoCapture(self.index, cv2.CAP_DSHOW)

        # Set video frame size
        frame_width = 800
        frame_height = 600
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)

        # Video frame configuration
        cv2.namedWindow('Video Frame', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Video Frame', frame_width, frame_height)

        # Variables to manage ROIs
        self.rois = []  # List to store all ROIs
        self.current_roi = None
        self.drawing = False
        self.selected_roi_index = -1

        # Load ROIs from file if available
        self.load_rois_from_file(f"ROI_CAM_{self.index}.txt")

        self.Video_Cap()

    # Mouse callback function to draw, resize, and delete ROIs
    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:  # Start drawing or selecting ROI
            self.drawing = True
            self.selected_roi_index = -1
            # Check if clicking on an existing ROI for resizing
            for i, (rx, ry, rw, rh) in enumerate(self.rois):
                if rx < x < rx + rw and ry < y < ry + rh:
                    self.selected_roi_index = i
                    break
            if self.selected_roi_index == -1:  # No ROI selected, start new ROI
                self.current_roi = [x, y, 0, 0]

        elif event == cv2.EVENT_MOUSEMOVE and self.drawing:  # Update ROI size
            if self.selected_roi_index == -1:  # Drawing a new ROI
                self.current_roi[2] = x - self.current_roi[0]
                self.current_roi[3] = y - self.current_roi[1]

        elif event == cv2.EVENT_LBUTTONUP:  # Finish drawing or resizing
            self.drawing = False
            if self.selected_roi_index == -1 and self.current_roi[2] > 0 and self.current_roi[3] > 0:
                self.rois.append(self.current_roi)  # Add new ROI if valid
            self.current_roi = None  # Clear current ROI when finished

        elif event == cv2.EVENT_RBUTTONDOWN:  # Right-click to delete the last created ROI
            if self.rois:
                self.rois.pop()  # Remove the last created ROI

    def save_rois_to_file(self, filename):
        """
        Save ROIs to a text file as a Python variable.
        """
        with open(filename, 'w') as file:
            file.write(f"ROI_CAM_{self.index} = {self.rois}")  # Save the list with a variable name
        print(f"ROIs saved to {filename}")

    def load_rois_from_file(self, filename):
        """
        Load ROIs from a text file if it exists.
        """
        if os.path.exists(filename):
            with open(filename, 'r') as file:
                try:
                    content = file.read()
                    # Extract the ROI variable from the file
                    roi_variable = f"ROI_CAM_{self.index}"
                    if roi_variable in content:
                        self.rois = ast.literal_eval(content.split('=')[1].strip())
                        print(f"ROIs loaded from {filename}: {self.rois}")
                except Exception as e:
                    print(f"Error loading ROIs: {e}")
        else:
            print(f"No ROI file found for camera {self.index}.")

    def Video_Cap(self):
        # Set mouse callback to the 'Video Frame' window
        cv2.setMouseCallback('Video Frame', self.mouse_callback)

        # Video display loop
        while True:
            ret, frame = self.cap.read()

            if not ret:
                break

            # Draw existing ROIs and label them
            for i, (x, y, w, h) in enumerate(self.rois):
                color = (0, 255, 0)  # Green for existing ROIs
                if i == self.selected_roi_index and self.drawing:  # Yellow if resizing or drawing
                    color = (0, 255, 255)
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                cv2.putText(frame, f'ROI {i + 1}', (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            # Draw the new ROI being created in yellow
            if self.current_roi and self.drawing:
                cv2.rectangle(frame, (self.current_roi[0], self.current_roi[1]),
                              (self.current_roi[0] + self.current_roi[2], self.current_roi[1] + self.current_roi[3]),
                              (0, 255, 255), 2)

            # Show frame with ROIs
            cv2.imshow('Video Frame', frame)

            # Condition to close the video frame
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):  # Press 'q' to quit
                break
            if cv2.getWindowProperty('Video Frame', cv2.WND_PROP_VISIBLE) < 1:
                break

        # Save ROIs to a file before exiting
        self.save_rois_to_file(f"ROI_CAM_{self.index}.txt")

        # Release camera and close windows
        self.cap.release()
        cv2.destroyAllWindows()