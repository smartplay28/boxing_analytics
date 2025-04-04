from datetime import datetime
from app.models.models import db, Session, Fighter, PunchData, Combination
from app.services.punch_detector import PunchDetector
from app.services.single_camera import SingleCameraRunner  # Updated import

class FightAnalyzer:
    def __init__(self, camera_id=0):
        self.detector = PunchDetector()
        self.active_sessions = {}  # session_id -> tracking info
        self.camera_runner = SingleCameraRunner(camera_id)
        
    def start_session(self, fighter_ids):
        """Start a new training/fight session"""
        session = Session(date=datetime.utcnow())
        session.fighters = Fighter.query.filter(Fighter.id.in_(fighter_ids)).all()
        db.session.add(session)
        db.session.commit()

        self.active_sessions[session.id] = {
            'start_time': datetime.utcnow(),
            'fighter_ids': fighter_ids,
            'punches': [],
            'combinations': {},
            'current_combo': {fighter_id: [] for fighter_id in fighter_ids}
        }

        self.camera_runner.start()
        return session.id

    def process_frame(self, session_id):
        """Process the latest frame from the camera"""
        if session_id not in self.active_sessions:
            return False

        result = self.camera_runner.get_latest_result()
        if not result:
            return False

        frame_time, frame, keypoints_list = result

        for person in keypoints_list:
            person_id = person['person_id']
            punch_data = self.detector.detect_punch_type(
                person['keypoints'], person_id, frame_time)

            if punch_data:
                fighter_ids = self.active_sessions[session_id]['fighter_ids']
                fighter_id = fighter_ids[person_id % len(fighter_ids)]  # Simple mapping

                db_punch_data = {
                    'fighter_id': fighter_id,
                    'punch_type': punch_data['type'],
                    'timestamp': punch_data['timestamp'],
                    'speed': punch_data['speed'],
                    'x_position': person['keypoints'][9][0] if person['keypoints'][9][2] > 0.3 else 0,
                    'y_position': person['keypoints'][9][1] if person['keypoints'][9][2] > 0.3 else 0
                }

                self.active_sessions[session_id]['punches'].append(db_punch_data)
                self._update_combinations(session_id, fighter_id, punch_data['type'], punch_data['timestamp'])

        # Periodically save punches
        if len(self.active_sessions[session_id]['punches']) > 10:
            self._save_punches(session_id)

        return True

    def end_session(self, session_id):
        if session_id not in self.active_sessions:
            return

        self._save_punches(session_id)
        self._finalize_combinations(session_id)
        self.camera_runner.stop()

        del self.active_sessions[session_id]

    def _save_punches(self, session_id):
        punches = self.active_sessions[session_id]['punches']
        for punch in punches:
            db.session.add(PunchData(**punch))
        db.session.commit()
        self.active_sessions[session_id]['punches'].clear()

    def _update_combinations(self, session_id, fighter_id, punch_type, timestamp):
        current_combo = self.active_sessions[session_id]['current_combo'][fighter_id]
        current_combo.append((punch_type, timestamp))

        # Example: Save combo if 3 or more punches within 3 seconds
        if len(current_combo) >= 3:
            time_diff = (current_combo[-1][1] - current_combo[0][1]).total_seconds()
            if time_diff <= 3:
                combo_str = "-".join([pt for pt, _ in current_combo])
                db.session.add(Combination(fighter_id=fighter_id, combo=combo_str, timestamp=timestamp))
                db.session.commit()
                current_combo.clear()

    def _finalize_combinations(self, session_id):
        for fighter_id, combo in self.active_sessions[session_id]['current_combo'].items():
            if combo:
                combo_str = "-".join([pt for pt, _ in combo])
                db.session.add(Combination(fighter_id=fighter_id, combo=combo_str, timestamp=datetime.utcnow()))
        db.session.commit()
