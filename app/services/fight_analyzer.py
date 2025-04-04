from datetime import datetime
import asyncio
from app.models.models import db, Session, Fighter, PunchData, Combination
from app.services.punch_detector import PunchDetector
from app.services.camera import AsyncSingleCameraRunner

class AsyncFightAnalyzer:
    def __init__(self, camera_id=0):
        self.detector = PunchDetector()
        self.active_sessions = {}
        self.camera_runner = AsyncSingleCameraRunner(camera_id)

    async def start_session(self, fighter_ids):
        """Start a new training/fight session"""
        session = Session(date=datetime.utcnow(), duration=0)
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

        await self.camera_runner.start()
        return session.id

    async def process_frame(self, session_id):
        """Process the latest frame from the camera"""
        if session_id not in self.active_sessions:
            return False

        result = self.camera_runner.get_latest_result()
        if not result:
            await asyncio.sleep(0.001)  # Yield if no frame is available
            return False

        frame_time, frame, keypoints_list = result

        for person in keypoints_list:
            person_id = person['person_id']
            punch_data = self.detector.detect_punch_type(
                person['keypoints'], person_id, frame_time)

            if punch_data:
                fighter_ids = self.active_sessions[session_id]['fighter_ids']
                fighter_id = fighter_ids[person_id % len(fighter_ids)]

                db_punch_data = {
                    'session_id': session_id,
                    'fighter_id': fighter_id,
                    'punch_type': punch_data['type'],
                    'timestamp': punch_data['timestamp'],
                    'speed': punch_data['speed'],
                    'x_position': person['keypoints'][9][0] if person['keypoints'][9][2] > 0.3 else 0,
                    'y_position': person['keypoints'][9][1] if person['keypoints'][9][2] > 0.3 else 0
                }

                self.active_sessions[session_id]['punches'].append(db_punch_data)
        
        # Periodically save punches (less frequent to reduce DB load)
        if len(self.active_sessions[session_id]['punches']) > 50:
            await self._save_punches(session_id)

        return True

    async def end_session(self, session_id):
        """End an active session and save all data"""
        if session_id not in self.active_sessions:
            return False

        start_time = self.active_sessions[session_id]['start_time']
        duration_seconds = (datetime.utcnow() - start_time).total_seconds()

        session = Session.query.get(session_id)
        if session:
            session.duration = int(duration_seconds)
            db.session.commit()

        await self._save_punches(session_id)
        await self._finalize_combinations(session_id)
        await self.camera_runner.stop()

        del self.active_sessions[session_id]
        return True

    async def _save_punches(self, session_id):
        """Save accumulated punches to database (using bulk insert)"""
        punches = self.active_sessions[session_id]['punches']
        if punches:
            punch_objs = [PunchData(**punch) for punch in punches]
            db.session.bulk_save_objects(punch_objs)
            db.session.commit()
            self.active_sessions[session_id]['punches'].clear()

    async def _update_combinations(self, session_id, fighter_id, punch_type, timestamp):
        """Track and update punch combinations"""
        current_combo = self.active_sessions[session_id]['current_combo'][fighter_id]
        
        # If the combo is empty or the time gap is too large, start a new combo
        if not current_combo or (timestamp - current_combo[-1][1]) > 1.5:  # 1.5 second gap breaks a combo
            current_combo.clear()
        
        current_combo.append((punch_type, timestamp))

        # Example: Save combo if 3 or more punches within 3 seconds
        if len(current_combo) >= 3:
            time_diff = current_combo[-1][1] - current_combo[0][1]
            if time_diff <= 3:
                combo_str = "-".join([pt for pt, _ in current_combo])
                
                # Use a subquery to efficiently check for existing combos
                existing = db.session.query(Combination).filter(
                    Combination.session_id == session_id,
                    Combination.fighter_id == fighter_id,
                    Combination.sequence == combo_str
                ).first()
                
                if existing:
                    existing.frequency += 1
                    existing.end_time = current_combo[-1][1]  # Update end time
                    db.session.commit()
                else:
                    # Create new combination
                    new_combo = Combination(
                        session_id=session_id,
                        fighter_id=fighter_id,
                        sequence=combo_str,
                        start_time=current_combo[0][1],
                        end_time=current_combo[-1][1],
                        frequency=1
                    )
                    db.session.add(new_combo)
                    db.session.commit()
            
            # Clear the combo after recording it
            current_combo.clear()

    async def _finalize_combinations(self, session_id):
        """Save any remaining combinations at the end of a session"""
        for fighter_id, combo in self.active_sessions[session_id]['current_combo'].items():
            if len(combo) >= 2:  # Only save combos with at least 2 punches
                combo_str = "-".join([pt for pt, _ in combo])
                
                # Use a subquery to efficiently check for existing combos
                existing = db.session.query(Combination).filter(
                    Combination.session_id == session_id,
                    Combination.fighter_id == fighter_id,
                    Combination.sequence == combo_str
                ).first()
                
                if existing:
                    existing.frequency += 1
                    existing.end_time = combo[-1][1]
                    db.session.commit()
                else:
                    new_combo = Combination(
                        session_id=session_id,
                        fighter_id=fighter_id,
                        sequence=combo_str,
                        start_time=combo[0][1],
                        end_time=combo[-1][1],
                        frequency=1
                    )
                    db.session.add(new_combo)
                    db.session.commit()