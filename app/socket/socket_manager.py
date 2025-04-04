from flask_socketio import SocketIO
from app.models.models import PunchData, Session, Fighter
import threading
import time

class SocketManager:
    def __init__(self, socketio):
        self.socketio = socketio
        self.active_sessions = {}
        self.monitor_thread = None
        self.running = False
        
    def register_handlers(self):
        """Register Socket.IO event handlers"""
        @self.socketio.on('connect')
        def handle_connect():
            print("Client connected")
            
        @self.socketio.on('disconnect')
        def handle_disconnect():
            print("Client disconnected")
            
        @self.socketio.on('get_updates')
        def handle_get_updates():
            print("Client requested updates")
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
            
    def stop_monitoring(self):
        """Stop the monitoring thread"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
            
    def _monitor_active_sessions(self):
        """Monitor active sessions and emit punch data"""
        last_punch_id = 0
        
        while self.running:
            try:
                # Get active sessions
                sessions = Session.query.order_by(Session.id.desc()).limit(1).all()
                
                if sessions:
                    session = sessions[0]
                    
                    # Get new punches since last check
                    new_punches = PunchData.query.filter(
                        PunchData.session_id == session.id,
                        PunchData.id > last_punch_id
                    ).order_by(PunchData.id).all()
                    
                    for punch in new_punches:
                        # Update last punch ID
                        if punch.id > last_punch_id:
                            last_punch_id = punch.id
                            
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
                            'hit_landed': True  # Placeholder - would need actual hit detection
                        })
                        
            except Exception as e:
                print(f"Error in monitoring thread: {e}")
                
            # Sleep to avoid overwhelming the database
            time.sleep(0.1)