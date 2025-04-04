import asyncio
from app import create_app
from flask_socketio import SocketIO
from flask_cors import CORS
from app.services.fight_analyzer import AsyncFightAnalyzer
from app.socket.socket_manager import SocketManager
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Create Flask app
app = create_app()
CORS(app)

# Initialize Socket.IO with async_mode='asyncio'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='asyncio')

# Initialize services (within the asyncio event loop)
async def initialize_services():
    global analyzer, socket_manager
    analyzer = AsyncFightAnalyzer(camera_id=0)
    socket_manager = SocketManager(socketio)
    socket_manager.register_handlers()

# Global session tracking
current_session_id = None
processing_active = False

async def frame_processing_loop():
    """Asynchronous loop for processing camera frames"""
    global processing_active, current_session_id
    try:
        while processing_active and current_session_id:
            await analyzer.process_frame(current_session_id)
            await asyncio.sleep(0.03)  # Aim for ~30 FPS processing rate
    except Exception as e:
        logging.error(f"Error in frame processing loop: {e}", exc_info=True)
    finally:
        processing_active = False  # Ensure loop terminates

@app.route('/')
def index():
    """Serve the main dashboard page"""
    return app.send_static_file('index.html')

@app.route('/start_session/<fighter_ids>', methods=['POST'])
async def start_session(fighter_ids):
    global current_session_id, processing_active
    
    # Parse fighter IDs
    try:
        fighter_id_list = [int(id) for id in fighter_ids.split(',')]
    except ValueError:
        return jsonify({'error': 'Invalid fighter IDs'}), 400
    
    try:
        # Start a new session
        current_session_id = await analyzer.start_session(fighter_id_list)
        
        # Start processing 
        processing_active = True
        asyncio.create_task(frame_processing_loop())
        socket_manager.start_monitoring()
        
        return jsonify({
            'session_id': current_session_id,
            'status': 'started'
        }), 200
    except Exception as e:
        logging.error(f"Error starting session: {e}", exc_info=True)
        return jsonify({'error': 'Could not start session'}), 500

@app.route('/end_session', methods=['POST'])
async def end_session():
    global current_session_id, processing_active
    
    if current_session_id:
        processing_active = False
        try:
            await analyzer.end_session(current_session_id)
            socket_manager.stop_monitoring()
            session_id = current_session_id
            current_session_id = None
            return jsonify({
                'session_id': session_id,
                'status': 'ended'
            }), 200
        except Exception as e:
            logging.error(f"Error ending session: {e}", exc_info=True)
            return jsonify({'error': 'Could not end session'}), 500
    else:
        return jsonify({'error': 'No active session'}), 404

if __name__ == '__main__':
    async def run_app():
        await initialize_services()  # Initialize services
        logging.info("Starting server on http://0.0.0.0:5000")
        await socketio.run(app, debug=app.config['DEBUG'], host='0.0.0.0', port=5000)

    asyncio.run(run_app())