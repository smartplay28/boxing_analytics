import cv2
import asyncio
import time
from app.services.punch_detector import PunchDetector
from app.utils.pose_utils import extract_keypoints, initialize_pose_model

class AsyncVideoGet:
    def __init__(self, src=0):
        self.src = src
        self.stream = None
        self.stopped = True
        self.frame = None

    async def start(self):
        self.stream = cv2.VideoCapture(self.src, cv2.CAP_DSHOW)
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
        self.stream.set(cv2.CAP_PROP_FPS, 15)
        self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.stopped = False
        await self.get()  # Start the frame grabbing

    async def get(self):
        while not self.stopped:
            ret, frame = self.stream.read()
            if ret:
                self.frame = frame
            await asyncio.sleep(0.001)  # Yield to the event loop

    async def stop(self):
        self.stopped = True
        if self.stream:
            self.stream.release()

class AsyncInferenceProcessor:
    def __init__(self, video_get, model, skip_frames=1):
        self.video_get = video_get
        self.stopped = False
        self.skip_frames = skip_frames
        self.frame_count = 0
        self.model = model
        self.latest_result = None

    async def start(self):
        asyncio.create_task(self.process())

    async def process(self):
        while not self.stopped:
            if self.video_get.frame is not None:
                self.frame_count += 1
                if self.frame_count % self.skip_frames == 0:
                    results = self.model(self.video_get.frame, verbose=False)[0]
                    self.latest_result = (time.time(), self.video_get.frame.copy(), results)
            await asyncio.sleep(0.001)

    def get_latest_result(self):
        return self.latest_result

    async def stop(self):
        self.stopped = True

class AsyncSingleCameraRunner:
    def __init__(self, camera_id=0):
        self.camera_id = camera_id
        self.video_get = AsyncVideoGet(camera_id)
        self.processor = None
        self.model, _ = initialize_pose_model()  # Initialize model once
        self.detector = PunchDetector()
        self.running = False

    async def start(self):
        self.running = True
        try:
            await self.video_get.start()
            self.processor = AsyncInferenceProcessor(self.video_get, self.model).start()
        except Exception as e:
            print(f"Error starting camera {self.camera_id}: {e}")
            await self.stop()  # Ensure resources are cleaned up
            return False
        return True

    async def stop(self):
        self.running = False
        if self.processor:
            self.processor.stopped = True  # Signal processor to stop
        if self.video_get:
            await self.video_get.stop()

    def get_latest_result(self):
        if self.processor:
            result = self.processor.get_latest_result()
            if result:
                timestamp, frame, results = result
                keypoints = extract_keypoints(results) if results else []
                return timestamp, frame, keypoints
        return None