from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from config import Config
from datetime import timedelta

# =============================
# Extension instantiation (global)
# =============================
db = SQLAlchemy()            # ORM
migrate = Migrate()          # Database migration handler
login = LoginManager()       # Login/session management
login.login_view = 'main.login'  # Redirect to 'main.login' if login required
csrf = CSRFProtect()         # CSRF protection for forms

# =============================
# Application factory
# =============================
def create_app():
    app = Flask(__name__)
    
    # Load configuration from config.py
    app.config.from_object(Config)

    # Initialize Flask extensions with the app context
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    csrf.init_app(app)

    # Register Jinja filter
    @app.template_filter('localtime')
    def localtime_filter(utc_dt):
        if utc_dt:
            return (utc_dt + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M')
        return ''

    # Blueprint registration and delayed imports
    with app.app_context():
        from app import models                      # Ensure models are registered
        from app.routes import main as main_bp      # Import and register blueprint
        app.register_blueprint(main_bp)

    return app

# =============================
# Flask-Login user loader
# =============================
@login.user_loader
def load_user(user_id):
    from app.models import User
    return db.session.get(User, int(user_id))  # Used to load user from session
