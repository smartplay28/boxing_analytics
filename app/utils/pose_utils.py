import numpy as np
from collections import deque

class PoseUtils:
    def __init__(self):
        self.prev_positions = {}
        self.positions_buffer = {}  # Store position history for smoother calculations
        self.buffer_length = 5  # Number of frames to keep in the buffer

    @staticmethod
    def calculate_angle(p1, p2, p3):
        """Calculates the angle between three points."""
        if any(p is None for p in [p1, p2, p3]):
            return 0  # Or handle this more gracefully

        v1 = np.array([p1[0] - p2[0], p1[1] - p2[1]])
        v2 = np.array([p3[0] - p2[0], p3[1] - p2[1]])

        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)

        if norm_v1 == 0 or norm_v2 == 0:
            return 0

        dot_product = np.dot(v1, v2)
        cosine_angle = dot_product / (norm_v1 * norm_v2)
        angle = np.degrees(np.arccos(np.clip(cosine_angle, -1.0, 1.0)))
        return angle

    def calculate_joint_speed(self, joint_name, position, frame_id):
        """Calculates the speed, velocity, and acceleration of a joint."""

        if joint_name not in self.positions_buffer:
            self.positions_buffer[joint_name] = deque(maxlen=self.buffer_length)
        
        self.positions_buffer[joint_name].append((frame_id, position))
        
        if len(self.positions_buffer[joint_name]) < 2:
            return 0, (0, 0), (0, 0)  # Not enough data yet

        
        (prev_frame_id, prev_position) = self.positions_buffer[joint_name][0]
        delta_time = frame_id - prev_frame_id
        
        if delta_time == 0:
            return 0, (0, 0), (0, 0)
        
        delta_x = position[0] - prev_position[0]
        delta_y = position[1] - prev_position[1]
        
        velocity = (delta_x / delta_time, delta_y / delta_time)
        speed = np.linalg.norm(velocity)
        
        acceleration = (0, 0)  # Initialize acceleration
        if len(self.positions_buffer[joint_name]) > 2:
            (prev_prev_frame_id, prev_prev_position) = self.positions_buffer[joint_name][1]
            prev_delta_time = prev_frame_id - prev_prev_frame_id
            if prev_delta_time != 0:
                prev_velocity_x = (prev_position[0] - prev_prev_position[0]) / prev_delta_time
                prev_velocity_y = (prev_position[1] - prev_prev_position[1]) / prev_delta_time
                acceleration = ((velocity[0] - prev_velocity_x) / delta_time, (velocity[1] - prev_velocity_y) / delta_time)
        
        return speed, velocity, acceleration