from flask import Flask
from app.config import Config
import logging

def create_app(config_object=Config):
    """
    Creates and configures the Flask application.

    Args:
        config_object: Configuration object to use for the app.

    Returns:
        The Flask application instance.
    """

    app = Flask(__name__)
    app.config.from_object(config_object)

    # Initialize logging
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info("Creating Flask app")

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
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        if not inspector.get_table_names():
            logging.info("Creating database tables")
            db.create_all()

    return app