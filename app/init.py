from flask import Flask
from config import Config  # Import the actual Config class
import os

def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    # Import and initialize database
    from app.models.models import db
    db.init_app(app)

    # Import blueprints inside function to avoid circular imports
    from app.routes.fighter_routes import fighter_bp
    from app.routes.session_routes import session_bp

    app.register_blueprint(fighter_bp, url_prefix='/api')
    app.register_blueprint(session_bp, url_prefix='/api')

    # Create database tables only if they don't exist
    with app.app_context():
        if not db.engine.table_names():  
            db.create_all()

    return app
