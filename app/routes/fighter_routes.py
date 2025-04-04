from flask import Blueprint, request, jsonify
from app.models.models import db, Fighter

fighter_bp = Blueprint('fighter', __name__)

@fighter_bp.route('/fighters', methods=['GET'])
def get_fighters():
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


@fighter_bp.route('/fighters/<int:fighter_id>', methods=['GET'])
def get_fighter(fighter_id):
    fighter = Fighter.query.get_or_404(fighter_id)
    return jsonify({
        'id': fighter.id,
        'name': fighter.name,
        'weight_class': fighter.weight_class,
        'height': fighter.height,
        'reach': fighter.reach,
        'stance': fighter.stance
    })


@fighter_bp.route('/fighters', methods=['POST'])
def create_fighter():
    data = request.get_json()

    required_fields = ['name', 'weight_class', 'height', 'reach', 'stance']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

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
        return jsonify({'error': str(e)}), 500


@fighter_bp.route('/fighters/<int:fighter_id>', methods=['PUT'])
def update_fighter(fighter_id):
    fighter = Fighter.query.get_or_404(fighter_id)
    data = request.get_json()

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
        return jsonify({'error': str(e)}), 500
