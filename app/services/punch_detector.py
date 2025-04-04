import numpy as np
from collections import deque
import time

class PunchDetector:
    def __init__(self):
        self.prev_positions = {}
        self.prev_velocities = {}  # Store velocity history
        self.prev_accelerations = {}  # Store acceleration history
        self.last_punch_time = {}
        self.cooldown = 0.5
        
        # Thresholds (adjust these based on your data)
        self.speed_threshold = 0.7
        self.velocity_threshold = 0.5  # Example threshold for velocity magnitude
        self.acceleration_threshold = 0.3  # Example threshold for acceleration magnitude
        self.direction_threshold = 30
        
    def detect_punch_type(self, keypoints, person_id, timestamp):
        """Detect if a punch was thrown and classify its type."""

        right_id = f"{person_id}_right"
        left_id = f"{person_id}_left"
        
        # Initialize tracking for this person if not already done
        if right_id not in self.prev_positions:
            self.prev_positions[right_id] = deque(maxlen=10)
            self.prev_velocities[right_id] = deque(maxlen=5)
            self.prev_accelerations[right_id] = deque(maxlen=3)
            self.last_punch_time[person_id] = 0
            
        if left_id not in self.prev_positions:
            self.prev_positions[left_id] = deque(maxlen=10)
            self.prev_velocities[left_id] = deque(maxlen=5)
            self.prev_accelerations[left_id] = deque(maxlen=3)
            
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
            
        # Calculate punch data for both hands
        right_punch_data = self._analyze_limb(keypoints_dict, 'right', right_id, timestamp)
        left_punch_data = self._analyze_limb(keypoints_dict, 'left', left_id, timestamp)
        
        # Determine which punch (if any) was thrown
        if right_punch_data and left_punch_data:
            # Both hands moved - use the one with highest combined motion
            right_motion = right_punch_data['speed'] + np.linalg.norm(right_punch_data['velocity']) + np.linalg.norm(right_punch_data['acceleration'])
            left_motion = left_punch_data['speed'] + np.linalg.norm(left_punch_data['velocity']) + np.linalg.norm(left_punch_data['acceleration'])
            if right_motion > left_motion:
                self.last_punch_time[person_id] = timestamp
                return right_punch_data
            else:
                self.last_punch_time[person_id] = timestamp
                return left_punch_data
        elif right_punch_data:
            self.last_punch_time[person_id] = timestamp
            return right_punch_data
        elif left_punch_data:
            self.last_punch_time[person_id] = timestamp
            return left_punch_data
            
        return None
        
    def _analyze_limb(self, keypoints, side, tracking_id, timestamp):
        """Analyze a single arm to detect punches."""

        shoulder = keypoints[f'{side}_shoulder']
        elbow = keypoints[f'{side}_elbow']
        wrist = keypoints[f'{side}_wrist']
        
        # Skip if any keypoint has low confidence
        if min(shoulder[2], elbow[2], wrist[2]) < 0.3:
            return None
            
        # Calculate wrist position and store in history
        position = wrist[:2]
        position_history = self.prev_positions[tracking_id]
        position_history.append((position, timestamp))
        
        # Need at least 2 frames to calculate speed, velocity, acceleration
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
        
        # Calculate velocity
        velocity = (pos2[0] - pos1[0]) / dt, (pos2[1] - pos1[1]) / dt
        velocity_history = self.prev_velocities[tracking_id]
        velocity_history.append(velocity)
        
        # Calculate acceleration (if enough data)
        acceleration = (0, 0) # Initialize acceleration
        if len(velocity_history) >= 2:
            vel1 = velocity_history[-2]
            vel2 = velocity_history[-1]
            acceleration = (vel2[0] - vel1[0]) / dt, (vel2[1] - vel1[1]) / dt
        acceleration_history = self.prev_accelerations[tracking_id]
        acceleration_history.append(acceleration)
        
        # Calculate average speed, velocity, acceleration
        avg_speed = np.mean(speed)
        avg_velocity = np.mean(velocity_history, axis=0) if velocity_history else (0, 0)
        avg_acceleration = np.mean(acceleration_history, axis=0) if acceleration_history else (0, 0)
        
        # Check if motion exceeds thresholds
        if avg_speed < self.speed_threshold or np.linalg.norm(avg_velocity) < self.velocity_threshold or np.linalg.norm(avg_acceleration) < self.acceleration_threshold:
            return None
            
        # Classify punch type
        punch_type = self._classify_punch(keypoints, side, position, position_history, avg_velocity, avg_acceleration)
        
        if punch_type:
            return {
                'type': punch_type,
                'timestamp': timestamp,
                'speed': avg_speed,
                'velocity': avg_velocity,
                'acceleration': avg_acceleration,
                'power': avg_speed * 1.2
            }
            
        return None
        
    def _classify_punch(self, keypoints, side, position, position_history, velocity, acceleration):
        """Classify the type of punch based on trajectory and arm position."""

        if len(position_history) < 2:
            return None
            
        prev_pos = position_history[-2][0]
        current_pos = position[0:2]
        
        # Calculate direction
        direction = np.array(current_pos) - np.array(prev_pos)
        if np.linalg.norm(direction) < 5:
            return None
            
        direction = direction / np.linalg.norm(direction)
        
        # Get arm angle
        shoulder = keypoints[f'{side}_shoulder'][:2]
        elbow = keypoints[f'{side}_elbow'][:2]
        wrist = keypoints[f'{side}_wrist'][:2]
        
        # Calculate elbow angle
        elbow_angle = self._calculate_angle(shoulder, elbow, wrist)
        
        # Classify based on side, direction and angle
        prefix = "Left" if side == "left" else "Right"
        
        # Check for uppercut - vertical movement and upward acceleration
        if direction[1] < -0.7 and acceleration[1] < -0.2:  # Adjust acceleration threshold
            return f"Uppercut {prefix}"
            
        # Check for straight - arm extended and linear movement
        if elbow_angle > 140 and abs(direction[0]) > 0.7 and abs(acceleration[0]) < 0.2:  # Adjust direction and acceleration
            return f"Straight {prefix}"
            
        # Check for hook - bent arm and curved trajectory
        if elbow_angle < 90 and abs(direction[0]) > 0.3 and abs(direction[1]) > 0.3:  # Adjust direction thresholds
            return f"Hook {prefix}"
            
        # Default to jab (quick, straight punch)
        if elbow_angle > 120 and abs(direction[0]) > 0.7 and np.linalg.norm(velocity) > self.velocity_threshold:
            return f"Jab {prefix}"
        
        return f"Other {prefix}"
        
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