from flask_socketio import SocketIO, emit
from app.models.models import PunchData, Session, Fighter, Combination
import threading
import time
import logging

class SocketManager:
    def __init__(self, socketio):
        self.socketio = socketio
        self.active_sessions = {}
        self.monitor_thread = None
        self.running = False
        self.last_punch_id = 0
        self.last_combo_id = 0
        
        # Configure logging (customize as needed)
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        
    def register_handlers(self):
        """Register Socket.IO event handlers"""
        @self.socketio.on('connect')
        def handle_connect():
            logging.info("Client connected")
            
        @self.socketio.on('disconnect')
        def handle_disconnect():
            logging.info("Client disconnected")
            
        @self.socketio.on('get_updates')
        def handle_get_updates():
            logging.info("Client requested updates")
            # Start sending updates if not already doing so
            if not self.running:
                self.start_monitoring()
                
    def start_monitoring(self):
        """Start the thread that monitors for new punches"""
        if self.monitor_thread is None or not self.monitor_thread.is_alive():
            self.running = True
            self.monitor_thread = threading.Thread(target=self._monitor_active_sessions)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            logging.info("Started monitoring thread")
            
    def stop_monitoring(self):
        """Stop the monitoring thread"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)  # Increased timeout
            if self.monitor_thread.is_alive():
                logging.warning("Monitoring thread did not terminate correctly")
            else:
                logging.info("Monitoring thread stopped")
            self.monitor_thread = None
            
    def _monitor_active_sessions(self):
        """Monitor active sessions and emit punch data"""
        while self.running:
            try:
                # Get active sessions (most recent)
                sessions = Session.query.order_by(Session.id.desc()).limit(1).all()
                
                if sessions:
                    session = sessions[0]
                    
                    # Get new punches since last check
                    new_punches = PunchData.query.filter(
                        PunchData.session_id == session.id,
                        PunchData.id > self.last_punch_id
                    ).order_by(PunchData.id).all()
                    
                    for punch in new_punches:
                        # Update last punch ID
                        if punch.id > self.last_punch_id:
                            self.last_punch_id = punch.id
                            
                        # Get fighter info
                        fighter = Fighter.query.get(punch.fighter_id)
                        
                        # Emit punch data
                        self.socketio.emit('punch_data', {
                            'punch_type': punch.punch_type,
                            'fighter_id': punch.fighter_id,
                            'fighter_name': fighter.name if fighter else "Unknown",
                            'timestamp': punch.timestamp,
                            'speed': punch.speed,
                            'power': punch.power if hasattr(punch, 'power') else None,
                            'hit_landed': True  # Placeholder
                        }, namespace='/')  # Specify namespace
                    
                    # Also emit combination data
                    new_combos = Combination.query.filter(
                        Combination.session_id == session.id,
                        Combination.id > self.last_combo_id
                    ).order_by(Combination.id).all()
                    
                    for combo in new_combos:
                        if combo.id > self.last_combo_id:
                            self.last_combo_id = combo.id
                            
                        fighter = Fighter.query.get(combo.fighter_id)
                        
                        self.socketio.emit('combo_data', {
                            'fighter_id': combo.fighter_id,
                            'fighter_name': fighter.name if fighter else "Unknown",
                            'sequence': combo.sequence,
                            'frequency': combo.frequency,
                            'start_time': combo.start_time,
                            'end_time': combo.end_time
                        }, namespace='/')  # Specify namespace
                        
                else:
                    logging.info("No active sessions found.")
                        
            except Exception as e:
                logging.error(f"Error in monitoring thread: {e}", exc_info=True)  # Log with traceback
                
            # Sleep to avoid overwhelming the database
            time.sleep(0.1)