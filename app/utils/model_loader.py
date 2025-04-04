# app/utils/model_loader.py

import torch
from ultralytics import YOLO
import numpy as np

def initialize_pose_model(model_name='yolov8n-pose.pt', device=None):
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    try:
        model = YOLO(model_name)
        model.conf = 0.25
        model.iou = 0.45
        model.agnostic = True

        dummy_frame = np.zeros((360, 480, 3), dtype=np.uint8)
        _ = model(dummy_frame, verbose=False)

        print(f"Model loaded successfully on {device}")
        return model, device

    except Exception as e:
        print(f"Error loading model: {e}")
        if device == "cuda" and torch.cuda.is_available():
            print("Attempting to load on CPU instead")
            return initialize_pose_model(model_name, "cpu")
        raise
