import os
import logging

class Config:
    """
    Configuration settings for the Flask application.
    """

    # Database configuration
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///fight_analytics.db')
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_key')
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() in ['true', '1']

    # Application-specific settings
    VIDEO_STORAGE_PATH = os.environ.get('VIDEO_STORAGE_PATH', 'videos')
    os.makedirs(VIDEO_STORAGE_PATH, exist_ok=True)  # Ensure folder exists

    CAMERA_IDS = os.environ.get('CAMERA_IDS', '')
    try:
        CAMERA_IDS = [int(x) for x in CAMERA_IDS.split(',') if x.isdigit()]
    except ValueError:
        logging.warning("Invalid CAMERA_IDS format. Using empty list.")
        CAMERA_IDS = []