import multiprocessing
from YOLODetector import YOLODetector
from PersonDetector import PersonDetector
import json

global_steps = {}
current_step = 1

# Load step data from a JSON file
def load_steps_data():
    with open("steps_data.json", "r") as file:
        return json.load(file)

def populate_global_steps():
    steps_data = load_steps_data()  # Load the steps data from JSON
    global global_steps
    for idx, step in enumerate(steps_data, start=1):
        camera_index = int(step["Camera"])
        roi = int(step["ROI"].split()[-1])  # Extract numeric part of "ROI X"
        obj = step["Object"]
        global_steps[idx] = [camera_index, roi, obj]
    print(f"Global Steps Populated: {global_steps}")

def run_person_detector(camera_index, queue):
    detector = PersonDetector()
    detector.run(camera_index, queue)

def run_yolo_detector(model_path, camera_index, threshold, queue):
    detector = YOLODetector(model_path)
    detector.run(camera_index=camera_index, threshold=threshold, queue=queue)

if __name__ == "__main__":
    person_camera_index = 0
    yolo_camera_index = 1
    yolo_model_path = "best.pt"

    detection_queue = multiprocessing.Queue()

    # Create and start the processes
    person_process = multiprocessing.Process(target=run_person_detector, args=(person_camera_index, detection_queue))
    yolo_process = multiprocessing.Process(target=run_yolo_detector, args=(yolo_model_path, yolo_camera_index, 0.7, detection_queue))

    person_process.start()
    yolo_process.start()

    try:
        # Populate the global steps
        populate_global_steps()
        print(f"Waiting for steps in sequence: {global_steps}")

        while current_step <= len(global_steps):
            # Retrieve a message from the queue
            message = detection_queue.get()
            converted_message = [message['camera_index'], message['roi'], message['object']]

            # Check if the converted message matches the current step
            expected_message = global_steps[current_step]
            if converted_message == expected_message:
                print(f"Step {current_step} Passed: {converted_message}")
                current_step += 1

            # Check if all steps are completed
            if current_step > len(global_steps):
                print("All Steps Completed")
                break

    except KeyboardInterrupt:
        print("Terminating...")
    finally:
        person_process.terminate()
        yolo_process.terminate()
