import eventlet
eventlet.monkey_patch()

from app import create_app
from flask_socketio import SocketIO
from flask_cors import CORS
from app.services.fight_analyzer import FightAnalyzer
from app.socket.socket_manager import SocketManager
import threading
import time

# Create Flask app
app = create_app()
CORS(app)

# Initialize Socket.IO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Initialize services
analyzer = FightAnalyzer(camera_id=0)
socket_manager = SocketManager(socketio)
socket_manager.register_handlers()

# Global session tracking
current_session_id = None
processing_thread = None
processing_active = False

def frame_processing_loop():
    """Background thread for processing camera frames"""
    global processing_active
    while processing_active and current_session_id:
        analyzer.process_frame(current_session_id)
        time.sleep(0.03)  # ~30 FPS processing rate

@app.route('/')
def index():
    """Serve the main dashboard page"""
    return app.send_static_file('index.html')

# Add routes to start and stop sessions
@app.route('/start_session/<fighter_ids>', methods=['POST'])
def start_session(fighter_ids):
    global current_session_id, processing_thread, processing_active
    
    # Parse fighter IDs
    fighter_id_list = [int(id) for id in fighter_ids.split(',')]
    
    # Start a new session
    current_session_id = analyzer.start_session(fighter_id_list)
    
    # Start processing in background thread
    processing_active = True
    processing_thread = threading.Thread(target=frame_processing_loop)
    processing_thread.daemon = True
    processing_thread.start()
    
    socket_manager.start_monitoring()
    
    return {'session_id': current_session_id, 'status': 'started'}

@app.route('/end_session', methods=['POST'])
def end_session():
    global current_session_id, processing_active
    
    if current_session_id:
        processing_active = False
        if processing_thread:
            processing_thread.join(timeout=1.0)
        
        analyzer.end_session(current_session_id)
        socket_manager.stop_monitoring()
        
        session_id = current_session_id
        current_session_id = None
        
        return {'session_id': session_id, 'status': 'ended'}
    
    return {'error': 'No active session'}, 404

if __name__ == '__main__':
    # Patch standard library for Socket.IO
    import eventlet
    eventlet.monkey_patch()
    
    # Start the server
    print("Starting server on http://0.0.0.0:5000")
    socketio.run(app, debug=app.config['DEBUG'], host='0.0.0.0', port=5000)