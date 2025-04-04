import torch
from ultralytics import YOLO
import numpy as np

def initialize_pose_model(model_name='yolov8n-pose.pt', device=None):
    """
    Initialize the YOLOv8 pose detection model
    
    Args:
        model_name: Name or path of the YOLOv8 model
        device: Device to run model on ('cuda' or 'cpu')
        
    Returns:
        model: Initialized YOLOv8 model
        device: Device the model is loaded on
    """
    # Set device
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    
    # Load the model
    try:
        model = YOLO(model_name)
        model.conf = 0.25  # Confidence threshold
        model.iou = 0.45   # IoU threshold
        model.agnostic = True
        model.to(device)
        
        # Pre-warm the model with a dummy prediction
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