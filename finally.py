import multiprocessing
from YOLODetector import YOLODetector
from PersonDetector import PersonDetector

def run_person_detector(camera_index):
    detector = PersonDetector()
    detector.run(camera_index)

def run_yolo_detector(model_path, camera_index, threshold):
    detector = YOLODetector(model_path)
    detector.run(camera_index=camera_index, threshold=threshold)

if __name__ == "__main__":
    # Define camera indices and model path
    person_camera_index = 0
    yolo_camera_index = 1
    yolo_model_path = "best.pt"

    # Create processes for running both detectors
    person_process = multiprocessing.Process(target=run_person_detector, args=(person_camera_index,))
    yolo_process = multiprocessing.Process(target=run_yolo_detector, args=(yolo_model_path, yolo_camera_index, 0.7))

    # Start the processes
    person_process.start()
    yolo_process.start()

    # Wait for both processes to complete
    person_process.join()
    yolo_process.join()
