import cv2

# Initialize camera (0-7)
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

# Video Frame Size Setting
frame_width = 800
frame_height = 600
cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)

# Video Frame Configuration
cv2.namedWindow('Video Frame', cv2.WINDOW_NORMAL)
cv2.resizeWindow('Video Frame', frame_width, frame_height)

# Variables to store ROI information
rois = []  # List to store all ROIs as [x, y, w, h]
current_roi = None
drawing = False
selected_roi_index = -1

# Mouse callback function to draw, resize, and delete ROIs
def mouse_callback(event, x, y, flags, param):
    global rois, current_roi, drawing, selected_roi_index

    if event == cv2.EVENT_LBUTTONDOWN:  # Start drawing or selecting ROI
        drawing = True
        selected_roi_index = -1
        # Check if clicking on an existing ROI for resizing
        for i, (rx, ry, rw, rh) in enumerate(rois):
            if rx < x < rx + rw and ry < y < ry + rh:
                selected_roi_index = i
                break
        if selected_roi_index == -1:  # No ROI selected, create new
            current_roi = [x, y, 0, 0]

    elif event == cv2.EVENT_MOUSEMOVE and drawing:  # Update ROI size
        if selected_roi_index == -1:  # Drawing a new ROI
            current_roi[2] = x - current_roi[0]
            current_roi[3] = y - current_roi[1]
        else:  # Resizing existing ROI
            rx, ry, rw, rh = rois[selected_roi_index]
            rois[selected_roi_index] = [rx, ry, x - rx, y - ry]

    elif event == cv2.EVENT_LBUTTONUP:  # Finish drawing or resizing
        drawing = False
        if selected_roi_index == -1 and current_roi[2] > 0 and current_roi[3] > 0:  # Add new ROI if valid
            rois.append(current_roi)
        current_roi = None  # Clear current ROI when finished

    elif event == cv2.EVENT_RBUTTONDOWN:  # Right click to delete the last created ROI
        if rois:
            rois.pop()  # Remove the last created ROI

# Set mouse callback to the 'Video Frame' window
cv2.setMouseCallback('Video Frame', mouse_callback)

# Video Display Loop
while True:
    ret, frame = cap.read()

    if not ret:
        break

    # Draw existing ROIs and label them
    for i, (x, y, w, h) in enumerate(rois):
        color = (0, 255, 0)  # Green for existing ROIs
        if i == selected_roi_index and drawing:  # Yellow if resizing or drawing
            color = (0, 255, 255)
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        cv2.putText(frame, f'ROI {i + 1}', (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # Draw the new ROI being created in yellow
    if current_roi and drawing:
        cv2.rectangle(frame, (current_roi[0], current_roi[1]), 
                             (current_roi[0] + current_roi[2], current_roi[1] + current_roi[3]), 
                             (0, 255, 255), 2)

    # Show frame with ROIs
    cv2.imshow('Video Frame', frame)

    # Condition to close the video frame (x button or 'q' is pressed)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    if cv2.getWindowProperty('Video Frame', cv2.WND_PROP_VISIBLE) < 1:
        break

# Release camera
cap.release()
cv2.destroyAllWindows()
