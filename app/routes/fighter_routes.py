from flask import Blueprint, request, jsonify
from app.models.models import db, Fighter
import logging

fighter_bp = Blueprint('fighter', __name__)

# Configure logging (you might want to customize this)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def validate_fighter_data(data):
    """Validates fighter data."""

    if not isinstance(data.get('name'), str) or not data.get('name').strip():
        return "Name must be a non-empty string", False
    if not isinstance(data.get('weight_class'), str) or not data.get('weight_class').strip():
        return "Weight class must be a non-empty string", False
    if not isinstance(data.get('height'), (int, float)):
        return "Height must be a number", False
    if not isinstance(data.get('reach'), (int, float)):
        return "Reach must be a number", False
    if not isinstance(data.get('stance'), str) or not data.get('stance').strip():
        return "Stance must be a non-empty string", False
    return None, True

@fighter_bp.route('/fighters', methods=['GET'])
def get_fighters():
    try:
        fighters = Fighter.query.all()
        return jsonify([
            {
                'id': f.id,
                'name': f.name,
                'weight_class': f.weight_class,
                'height': f.height,
                'reach': f.reach,
                'stance': f.stance
            } for f in fighters
        ])
    except Exception as e:
        logging.error(f"Error fetching fighters: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@fighter_bp.route('/fighters/<int:fighter_id>', methods=['GET'])
def get_fighter(fighter_id):
    try:
        fighter = Fighter.query.get_or_404(fighter_id)
        return jsonify({
            'id': fighter.id,
            'name': fighter.name,
            'weight_class': fighter.weight_class,
            'height': fighter.height,
            'reach': fighter.reach,
            'stance': fighter.stance
        })
    except Exception as e:
        logging.error(f"Error fetching fighter {fighter_id}: {e}")
        return jsonify({'error': 'Fighter not found'}), 404


@fighter_bp.route('/fighters', methods=['POST'])
def create_fighter():
    data = request.get_json()

    # Validate data
    error_message, is_valid = validate_fighter_data(data)
    if not is_valid:
        return jsonify({'error': error_message}), 400

    try:
        fighter = Fighter(
            name=data['name'],
            weight_class=data['weight_class'],
            height=float(data['height']),
            reach=float(data['reach']),
            stance=data['stance']
        )
        db.session.add(fighter)
        db.session.commit()

        return jsonify({
            'id': fighter.id,
            'name': fighter.name,
            'weight_class': fighter.weight_class,
            'height': fighter.height,
            'reach': fighter.reach,
            'stance': fighter.stance
        }), 201
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating fighter: {e}")
        return jsonify({'error': 'Could not create fighter'}), 500


@fighter_bp.route('/fighters/<int:fighter_id>', methods=['PUT'])
def update_fighter(fighter_id):
    fighter = Fighter.query.get_or_404(fighter_id)
    data = request.get_json()

    # Validate data (partial update, so some fields might be missing)
    error_message, is_valid = validate_fighter_data(data)
    if not is_valid and error_message != "All fields are valid":
        return jsonify({'error': error_message}), 400

    try:
        fighter.name = data.get('name', fighter.name)
        fighter.weight_class = data.get('weight_class', fighter.weight_class)
        fighter.height = float(data.get('height', fighter.height))
        fighter.reach = float(data.get('reach', fighter.reach))
        fighter.stance = data.get('stance', fighter.stance)

        db.session.commit()

        return jsonify({
            'id': fighter.id,
            'name': fighter.name,
            'weight_class': fighter.weight_class,
            'height': fighter.height,
            'reach': fighter.reach,
            'stance': fighter.stance
        })
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating fighter {fighter_id}: {e}")
        return jsonify({'error': 'Could not update fighter'}), 500