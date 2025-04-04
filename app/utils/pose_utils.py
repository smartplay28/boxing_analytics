import cv2
import numpy as np
import torch
from ultralytics import YOLO
from collections import deque

# =========================
# Model Initialization
# =========================

def initialize_pose_model(model_name='yolov8n-pose.pt', device=None):
    model = YOLO(model_name)
    model.conf = 0.25
    model.iou = 0.45
    model.agnostic = True

    # Set device
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)

    # Pre-warm the model
    dummy_frame = np.zeros((360, 480, 3), dtype=np.uint8)
    _ = model(dummy_frame, verbose=False)

    return model, device

# =========================
# Pose Utilities
# =========================

def detect_pose(frame, model):
    if torch.cuda.is_available():
        with torch.cuda.amp.autocast():
            results = model(frame, verbose=False)
    else:
        results = model(frame, verbose=False)
    return results

def extract_keypoints(results):
    keypoints_list = []
    if results and results[0].keypoints is not None:
        keypoints = results[0].keypoints.data
        for idx, kpt in enumerate(keypoints):
            person_keypoints = kpt.cpu().numpy()
            keypoints_list.append({
                'person_id': idx,
                'keypoints': person_keypoints
            })
    return keypoints_list

def draw_pose(frame, keypoints, reduced_drawing=True):
    if reduced_drawing:
        for person in keypoints:
            kpt_np = person['keypoints']
            for i in [5, 6, 7, 8, 9, 10]:  # Shoulders, elbows, wrists
                if i < len(kpt_np) and kpt_np[i][2] > 0.3:
                    cv2.circle(frame, 
                               (int(kpt_np[i][0]), int(kpt_np[i][1])), 
                               5, (0, 255, 0), -1)
    return frame

# =========================
# Angle Calculations
# =========================

def calculate_angle(a, b, c):
    """Returns angle (in degrees) between points a, b, c where b is the vertex."""
    a, b, c = np.array(a[:2]), np.array(b[:2]), np.array(c[:2])
    ab = a - b
    cb = c - b
    cosine_angle = np.dot(ab, cb) / (np.linalg.norm(ab) * np.linalg.norm(cb) + 1e-6)
    angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
    return np.degrees(angle)

def calculate_angles(keypoints, limb='right_arm'):
    if keypoints is None or len(keypoints) < 13:
        return None

    if limb == 'right_arm':
        shoulder = keypoints[5]
        elbow = keypoints[7]
        wrist = keypoints[9]
    elif limb == 'left_arm':
        shoulder = keypoints[6]
        elbow = keypoints[8]
        wrist = keypoints[10]
    else:
        return None

    if min(shoulder[2], elbow[2], wrist[2]) < 0.3:
        return None

    return calculate_angle(shoulder, elbow, wrist)

# =========================
# Named Keypoints Extractor
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
# Keypoint Smoothing (Optional)
# =========================

class KeypointSmoother:
    def __init__(self, maxlen=5):
        self.buffer = deque(maxlen=maxlen)

    def update(self, keypoints):
        self.buffer.append(keypoints)
        return np.mean(self.buffer, axis=0)
