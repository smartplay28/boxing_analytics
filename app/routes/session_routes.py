from flask import Blueprint, request, jsonify
from app.models.models import db, Session, Fighter, PunchData, Combination
from app.services.fight_analyzer import AsyncFightAnalyzer
from datetime import datetime
import asyncio
import logging

session_bp = Blueprint('session', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def validate_session_data(data):
    """Validates session data."""
    if not isinstance(data.get('fighter_ids'), list) or not data.get('fighter_ids'):
        return "fighter_ids must be a non-empty list", False
    return None, True

@session_bp.route('/sessions', methods=['POST'])
def start_session():
    data = request.get_json()

    # Validate data
    error_message, is_valid = validate_session_data(data)
    if not is_valid:
        return jsonify({'error': error_message}), 400

    fighter_ids = data.get('fighter_ids')

    try:
        fighters = Fighter.query.filter(Fighter.id.in_(fighter_ids)).all()
        if len(fighters) != len(fighter_ids):
            return jsonify({'error': 'One or more fighter IDs are invalid'}), 400

        analyzer = AsyncFightAnalyzer()  # Instantiate within the route
        session_id = asyncio.run(analyzer.start_session(fighter_ids))
        return jsonify({
            'session_id': session_id,
            'start_time': datetime.utcnow().isoformat(),
            'fighter_ids': fighter_ids
        }), 201
    except Exception as e:
        logging.error(f"Error starting session: {e}")
        return jsonify({'error': 'Could not start session'}), 500


@session_bp.route('/sessions/<int:session_id>/end', methods=['POST'])
def end_session(session_id):
    try:
        analyzer = AsyncFightAnalyzer()  # Instantiate within the route
        success = asyncio.run(analyzer.end_session(session_id))
        if not success:
            return jsonify({'error': 'Session not found or already ended'}), 404

        return jsonify({
            'session_id': session_id,
            'status': 'ended',
            'end_time': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logging.error(f"Error ending session {session_id}: {e}")
        return jsonify({'error': 'Could not end session'}), 500


@session_bp.route('/sessions/<int:session_id>', methods=['GET'])
def get_session(session_id):
    try:
        session = Session.query.get_or_404(session_id)

        punches_by_fighter = {}
        for fighter in session.fighters:
            punches = PunchData.query.filter_by(session_id=session_id, fighter_id=fighter.id).all()

            punch_types = {}
            for punch in punches:
                punch_types[punch.punch_type] = punch_types.get(punch.punch_type, 0) + 1

            punches_by_fighter[fighter.id] = {
                'name': fighter.name,
                'total_punches': len(punches),
                'punch_types': punch_types
            }

        combinations = Combination.query.filter_by(session_id=session_id).all()
        combo_stats = {}
        for combo in combinations:
            combo_stats.setdefault(combo.fighter_id, []).append({
                'sequence': combo.sequence,
                'frequency': combo.frequency
            })

        return jsonify({
            'id': session.id,
            'date': session.date.isoformat(),
            'duration': session.duration,
            'fighters': [{'id': f.id, 'name': f.name} for f in session.fighters],
            'punch_stats': punches_by_fighter,
            'combination_stats': combo_stats
        })
    except Exception as e:
        logging.error(f"Error getting session {session_id}: {e}")
        return jsonify({'error': 'Could not retrieve session'}), 500


@session_bp.route('/sessions', methods=['GET'])
def get_sessions():
    try:
        sessions = Session.query.all()
        return jsonify([
            {
                'id': s.id,
                'date': s.date.isoformat(),
                'duration': s.duration,
                'fighters': [{'id': f.id, 'name': f.name} for f in s.fighters]
            }
            for s in sessions
        ])
    except Exception as e:
        logging.error(f"Error getting all sessions: {e}")
        return jsonify({'error': 'Could not retrieve sessions'}), 500


@session_bp.route('/sessions/<int:session_id>/punches', methods=['GET'])
def get_session_punches(session_id):
    fighter_id = request.args.get('fighter_id', type=int)

    try:
        query = PunchData.query.filter_by(session_id=session_id)
        if fighter_id:
            query = query.filter_by(fighter_id=fighter_id)

        punches = query.all()

        return jsonify([
            {
                'id': p.id,
                'fighter_id': p.fighter_id,
                'punch_type': p.punch_type,
                'timestamp': p.timestamp,
                'speed': p.speed,
                'x_position': p.x_position,
                'y_position': p.y_position
            } for p in punches
        ])
    except Exception as e:
        logging.error(f"Error getting punches for session {session_id}: {e}")
        return jsonify({'error': 'Could not retrieve punches'}), 500