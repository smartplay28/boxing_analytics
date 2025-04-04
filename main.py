from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit
from app.services.fight_analyzer import FightAnalyzer
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

analyzer = FightAnalyzer(camera_id=0)
session_id = None


@app.route('/start_session', methods=['POST'])
def start_session():
    global session_id
    data = request.get_json()
    fighter_ids = data.get('fighter_ids', [1, 2])
    session_id = analyzer.start_session(fighter_ids)
    return jsonify({'session_id': session_id})


@socketio.on('get_updates')
def send_punch_updates():
    global session_id
    if not session_id:
        return

    if analyzer.process_frame(session_id):
        punches = analyzer.active_sessions[session_id]['punches']
        if punches:
            latest = punches[-1]
            emit('punch_data', latest)


if __name__ == '__main__':
    import eventlet
    eventlet.monkey_patch()
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)

