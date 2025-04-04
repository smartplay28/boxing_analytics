from app import create_app
from flask_socketio import SocketIO
from flask_cors import CORS
from app.services.fight_analyzer import FightAnalyzer
from app.socket.socket_manager import SocketManager

# Create Flask app
app = create_app()
CORS(app)

# Initialize Socket.IO
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize services
analyzer = FightAnalyzer(camera_id=0)
socket_manager = SocketManager(socketio)
socket_manager.register_handlers()

# Global session tracking
current_session_id = None

@app.route('/')
def index():
    """Serve the main dashboard page"""
    return app.send_static_file('index.html')

if __name__ == '__main__':
    # Patch standard library for Socket.IO
    import eventlet
    eventlet.monkey_patch()
    
    # Start the server
    print("Starting server on http://0.0.0.0:5000")
    socketio.run(app, debug=app.config['DEBUG'], host='0.0.0.0', port=5000)