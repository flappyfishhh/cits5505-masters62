from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf import CSRFProtect

# Initialize Flask extensions (but don't bind to app yet)
db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'main.login' # Redirect unauthorized users to this view
csrf = CSRFProtect()

def create_app():
    # Create Flask application instance
    app = Flask(__name__)
    app.config.from_object('config.Config') # Load configuration from config.py

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    csrf.init_app(app)

    with app.app_context():
        # Import modules here to avoid circular imports
        from app import models
        from app.routes import main as main_bp
        app.register_blueprint(main_bp) # Register routes with blueprint

    return app

# Load user callback for Flask-Login
@login.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id)) # Return the user object by ID
