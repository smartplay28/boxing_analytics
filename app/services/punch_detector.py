import numpy as np
from collections import deque
import time

class PunchDetector:
    def __init__(self):
        self.prev_positions = {}  # person_id -> deque of wrist positions
        self.prev_speeds = {}     # person_id -> deque of speeds
        self.last_punch_time = {} # person_id -> timestamp of last punch
        self.cooldown = 0.5       # seconds between punches
        
        # Thresholds
        self.speed_threshold = 0.7    # m/s, minimum speed to count as a punch
        self.direction_threshold = 30  # degrees, max deviation from expected angle
        
    def detect_punch_type(self, keypoints, person_id, timestamp):
        """Detect if a punch was thrown and classify its type."""
        # Create unique IDs for left and right hands
        right_id = f"{person_id}_right"
        left_id = f"{person_id}_left"
        
        # Initialize tracking for this person if not already done
        if right_id not in self.prev_positions:
            self.prev_positions[right_id] = deque(maxlen=10)
            self.prev_speeds[right_id] = deque(maxlen=5)
            self.last_punch_time[person_id] = 0
            
        if left_id not in self.prev_positions:
            self.prev_positions[left_id] = deque(maxlen=10)
            self.prev_speeds[left_id] = deque(maxlen=5)
            
        # Check cooldown
        if timestamp - self.last_punch_time.get(person_id, 0) < self.cooldown:
            return None
            
        # Get relevant keypoints
        keypoints_dict = self._get_named_keypoints(keypoints)
        
        # Check if all required keypoints are present
        required = ['right_shoulder', 'right_elbow', 'right_wrist', 
                    'left_shoulder', 'left_elbow', 'left_wrist']
        if not all(k in keypoints_dict and keypoints_dict[k][2] > 0.3 for k in required):
            return None
            
        # Calculate punch speed and direction for both hands
        right_punch = self._analyze_limb(keypoints_dict, 'right', right_id, timestamp)
        left_punch = self._analyze_limb(keypoints_dict, 'left', left_id, timestamp)
        
        # Determine which punch (if any) was thrown
        if right_punch and left_punch:
            # Both hands moved - use the faster one
            if right_punch['speed'] > left_punch['speed']:
                self.last_punch_time[person_id] = timestamp
                return right_punch
            else:
                self.last_punch_time[person_id] = timestamp
                return left_punch
        elif right_punch:
            self.last_punch_time[person_id] = timestamp
            return right_punch
        elif left_punch:
            self.last_punch_time[person_id] = timestamp
            return left_punch
            
        return None
        
    def _analyze_limb(self, keypoints, side, tracking_id, timestamp):
        """Analyze a single arm to detect punches."""
        # Get relevant keypoints
        shoulder = keypoints[f'{side}_shoulder']
        elbow = keypoints[f'{side}_elbow']
        wrist = keypoints[f'{side}_wrist']
        
        # Skip if any keypoint has low confidence
        if min(shoulder[2], elbow[2], wrist[2]) < 0.3:
            return None
            
        # Calculate wrist position and store in history
        position = wrist[:2]  # x, y
        position_history = self.prev_positions[tracking_id]
        position_history.append((position, timestamp))
        
        # Need at least 2 frames to calculate speed
        if len(position_history) < 2:
            return None
            
        # Calculate speed (px/s)
        pos1, t1 = position_history[-2]
        pos2, t2 = position_history[-1]
        dt = t2 - t1
        if dt <= 0:
            return None
            
        distance = np.linalg.norm(np.array(pos2) - np.array(pos1))
        speed = distance / dt
        
        speed_history = self.prev_speeds[tracking_id]
        speed_history.append(speed)
        
        # Calculate average speed
        avg_speed = sum(speed_history) / len(speed_history)
        
        # Check if speed exceeds threshold
        if avg_speed < self.speed_threshold:
            return None
            
        # Classify punch type based on arm position and movement
        punch_type = self._classify_punch(keypoints, side, position, position_history)
        
        if punch_type:
            return {
                'type': punch_type,
                'timestamp': timestamp,
                'speed': avg_speed,
                'power': avg_speed * 1.2  # Simple power estimation
            }
            
        return None
        
    def _classify_punch(self, keypoints, side, position, position_history):
        """Classify the type of punch based on trajectory and arm position."""
        # Get previous position to determine direction
        if len(position_history) < 2:
            return None
            
        prev_pos = position_history[-2][0]
        current_pos = position[0:2]
        
        # Calculate direction
        direction = np.array(current_pos) - np.array(prev_pos)
        if np.linalg.norm(direction) < 5:  # Minimum movement threshold
            return None
            
        # Normalize direction vector
        direction = direction / np.linalg.norm(direction)
        
        # Get arm angle
        shoulder = keypoints[f'{side}_shoulder'][:2]
        elbow = keypoints[f'{side}_elbow'][:2]
        wrist = keypoints[f'{side}_wrist'][:2]
        
        # Calculate elbow angle
        elbow_angle = self._calculate_angle(shoulder, elbow, wrist)
        
        # Classify based on side, direction and angle
        prefix = "Left" if side == "left" else "Right"
        
        # Check for uppercut - vertical movement
        if direction[1] < -0.7:  # Moving upward (screen coordinates)
            return f"Uppercut {prefix}"
            
        # Check for straight - arm extended
        if elbow_angle > 140:
            return f"Straight {prefix}"
            
        # Default to hook
        return f"Hook {prefix}"
        
    def _calculate_angle(self, a, b, c):
        """Calculate angle between three points in degrees."""
        ba = np.array(a) - np.array(b)
        bc = np.array(c) - np.array(b)
        
        cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
        angle = np.arccos(np.clip(cosine, -1.0, 1.0))
        return np.degrees(angle)
        
    def _get_named_keypoints(self, keypoints):
        """Convert numeric keypoints to named keypoints."""
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