from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Fighter(db.Model):
    __tablename__ = 'fighters'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    weight_class = db.Column(db.String(50), nullable=False)
    height = db.Column(db.Float, nullable=False)  # in cm or inches
    reach = db.Column(db.Float, nullable=False)   # in cm or inches
    stance = db.Column(db.String(20), nullable=False)  # orthodox, southpaw, etc.
    sessions = db.relationship('Session', secondary='session_fighters', back_populates='fighters')

    def __repr__(self):
        return f"<Fighter {self.name} ({self.stance})>"


class Session(db.Model):
    __tablename__ = 'sessions'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    duration = db.Column(db.Integer, nullable=False)  # in seconds
    fighters = db.relationship('Fighter', secondary='session_fighters', back_populates='sessions')
    punches = db.relationship('PunchData', backref='session', cascade='all, delete-orphan')
    combinations = db.relationship('Combination', backref='session', cascade='all, delete-orphan')
    videos = db.relationship('Video', backref='session', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Session {self.id} on {self.date.strftime('%Y-%m-%d')}>"


# Junction table for many-to-many relationship
session_fighters = db.Table(
    'session_fighters',
    db.Column('session_id', db.Integer, db.ForeignKey('sessions.id'), primary_key=True, index=True),
    db.Column('fighter_id', db.Integer, db.ForeignKey('fighters.id'), primary_key=True, index=True)
)


class PunchData(db.Model):
    __tablename__ = 'punch_data'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False, index=True)
    fighter_id = db.Column(db.Integer, db.ForeignKey('fighters.id'), nullable=False, index=True)
    punch_type = db.Column(db.String(50), nullable=False)  # jab, cross, hook, uppercut, etc.
    timestamp = db.Column(db.Float, nullable=False)  # seconds from start
    speed = db.Column(db.Float, nullable=False)      # in m/s
    power = db.Column(db.Float)                      # optional power metric
    x_position = db.Column(db.Float, nullable=False)
    y_position = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<Punch {self.punch_type} at {self.timestamp}s by Fighter {self.fighter_id}>"


class Combination(db.Model):
    __tablename__ = 'combinations'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False, index=True)
    fighter_id = db.Column(db.Integer, db.ForeignKey('fighters.id'), nullable=False, index=True)
    sequence = db.Column(db.String(100), nullable=False)  # e.g. "jab-cross-hook"
    start_time = db.Column(db.Float, nullable=False)
    end_time = db.Column(db.Float, nullable=False)
    frequency = db.Column(db.Integer, default=1)

    def __repr__(self):
        return f"<Combo {self.sequence} (x{self.frequency})>"


class Video(db.Model):
    __tablename__ = 'videos'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False, index=True)
    camera_id = db.Column(db.Integer, nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # in seconds

    def __repr__(self):
        return f"<Video Camera {self.camera_id} for Session {self.session_id}>"
