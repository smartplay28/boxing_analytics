from flask import Flask
from app.config import Config

def create_app(config_object=Config):
    # Create and configure the app
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
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        if not inspector.get_table_names():
            print("Creating database tables...")
            db.create_all()

    return app