import cv2
import numpy as np
import torch
from ultralytics import YOLO
from collections import deque

# =========================
# Model Initialization
# =========================

def initialize_pose_model(model_name='yolov8n-pose.pt', device=None):
    """
    Loads the YOLOv8 pose model.
    """
    model = YOLO(model_name)
    model.conf = 0.25
    model.iou = 0.45
    model.agnostic = True

    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)

    dummy_frame = np.zeros((360, 480, 3), dtype=np.uint8)
    _ = model(dummy_frame, verbose=False)

    return model, device

# =========================
# Pose Detection
# =========================

def detect_pose(frame, model):
    """
    Runs pose detection on a frame.
    """
    if torch.cuda.is_available():
        with torch.cuda.amp.autocast():
            results = model(frame, verbose=False)
    else:
        results = model(frame, verbose=False)
    return results

def extract_keypoints(results):
    """
    Extracts keypoints from model results.
    """
    keypoints_list = []
    if results and hasattr(results[0], 'keypoints') and results[0].keypoints is not None:
        keypoints = results[0].keypoints.data
        for idx, kpt in enumerate(keypoints):
            keypoints_list.append({
                'person_id': idx,
                'keypoints': kpt.cpu().numpy()
            })
    return keypoints_list

# =========================
# Drawing Utilities
# =========================

def draw_pose(frame, keypoints, reduced=True):
    """
    Draws selected keypoints on the frame.
    """
    if reduced:
        for person in keypoints:
            kpt_np = person['keypoints']
            for i in [5, 6, 7, 8, 9, 10]:
                if i < len(kpt_np) and kpt_np[i][2] > 0.3:
                    cv2.circle(frame, 
                               (int(kpt_np[i][0]), int(kpt_np[i][1])), 
                               5, (0, 255, 0), -1)
    return frame

# =========================
# Angle Calculations
# =========================

def calculate_angle(a, b, c):
    a, b, c = np.array(a[:2]), np.array(b[:2]), np.array(c[:2])
    ab = a - b
    cb = c - b
    cosine_angle = np.dot(ab, cb) / (np.linalg.norm(ab) * np.linalg.norm(cb) + 1e-6)
    angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
    return np.degrees(angle)

def calculate_limb_angle(keypoints, limb='right_arm'):
    """
    Calculates elbow angle for left or right arm.
    """
    if keypoints is None or len(keypoints) < 13:
        return None

    if limb == 'right_arm':
        shoulder, elbow, wrist = keypoints[5], keypoints[7], keypoints[9]
    elif limb == 'left_arm':
        shoulder, elbow, wrist = keypoints[6], keypoints[8], keypoints[10]
    else:
        return None

    if min(shoulder[2], elbow[2], wrist[2]) < 0.3:
        return None

    return calculate_angle(shoulder, elbow, wrist)

# =========================
# Named Keypoints
# =========================

def get_named_keypoints(keypoints):
    return {
        'nose': keypoints[0],
        'right_shoulder': keypoints[5],
        'left_shoulder': keypoints[6],
        'right_elbow': keypoints[7],
        'left_elbow': keypoints[8],
        'right_wrist': keypoints[9],
        'left_wrist': keypoints[10],
        'right_hip': keypoints[11],
        'left_hip': keypoints[12],
    }

# =========================
# Smoothing
# =========================

class KeypointSmoother:
    def __init__(self, maxlen=5):
        self.buffer = deque(maxlen=maxlen)

    def update(self, keypoints):
        if keypoints is not None:
            self.buffer.append(keypoints)
            return np.mean(self.buffer, axis=0)
        return None
