import cv2
import threading
import time
import queue
from app.services.punch_detector import PunchDetector
from app.utils.pose_utils import detect_pose, extract_keypoints
from app.utils.model_loader import initialize_pose_model  # Assumed location

class VideoGet:
    def __init__(self, src=0):
        self.stream = cv2.VideoCapture(src)
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
        self.stream.set(cv2.CAP_PROP_FPS, 15)
        self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.stopped = False
        self.frame = None

    def start(self):
        threading.Thread(target=self.get, daemon=True).start()
        return self

    def get(self):
        while not self.stopped:
            ret, frame = self.stream.read()
            if ret:
                self.frame = frame

    def stop(self):
        self.stopped = True
        self.stream.release()


class InferenceProcessor:
    def __init__(self, frame_queue, result_queue, model, skip_frames=2):
        self.frame_queue = frame_queue
        self.result_queue = result_queue
        self.stopped = False
        self.skip_frames = skip_frames
        self.frame_count = 0
        self.model = model

    def start(self):
        threading.Thread(target=self.process, daemon=True).start()
        return self

    # In the process method of InferenceProcessor
    def process(self):
        while not self.stopped:
            if not self.frame_queue.empty():
                self.frame_count += 1
                timestamp, frame = self.frame_queue.get()
            
            if self.frame_count % self.skip_frames != 0:
                continue

            pose_results = detect_pose(frame, self.model)
            self.result_queue.put((timestamp, frame, pose_results))

    def stop(self):
        self.stopped = True


class SingleCameraRunner:
    def __init__(self, camera_id=0):
        self.model, self.device = initialize_pose_model()
        self.video_get = VideoGet(camera_id).start()
        self.frame_queue = queue.Queue(maxsize=2)
        self.result_queue = queue.Queue(maxsize=2)
        self.processor = InferenceProcessor(self.frame_queue, self.result_queue, self.model, skip_frames=1).start()
        self.detector = PunchDetector()
        self.running = False

    def start(self):
        self.running = True
        threading.Thread(target=self._gather_frames, daemon=True).start()

    def _gather_frames(self):
        while self.running:
            if self.video_get.frame is not None:
                timestamp = time.time()
                if not self.frame_queue.full():
                    self.frame_queue.put((timestamp, self.video_get.frame.copy()))
            time.sleep(0.001)

    def get_latest_result(self):
        if not self.result_queue.empty():
            timestamp, frame, pose = self.result_queue.get()
            keypoints = extract_keypoints(pose) if pose else []
            return timestamp, frame, keypoints
        return None

    def stop(self):
        self.running = False
        self.video_get.stop()
        self.processor.stop()
