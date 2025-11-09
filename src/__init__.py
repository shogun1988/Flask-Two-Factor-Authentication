from decouple import config
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager # Add this line
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect

app = Flask(__name__)
# Load config object from environment, falling back to a sensible default for local dev
app.config.from_object(config("APP_SETTINGS", default="config.DevelopmentConfig"))

bcrypt = Bcrypt(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager()  # Add this line
login_manager.init_app(app)  # Add this line

# Registering blueprints
from src.accounts.views import accounts_bp
from src.core.views import core_bp

app.register_blueprint(accounts_bp)
app.register_blueprint(core_bp)

# Development convenience: if database is brand new (no tables), create base tables.
# This prevents 500 errors like "no such table: users" before running migrations.
# In production environments, rely solely on migrations; remove this block if undesired.
with app.app_context():
    try:
        inspector = inspect(db.engine)
        if 'users' not in inspector.get_table_names():
            db.create_all()
    except Exception:
        # Fail silently; proper errors will surface at query time.
        pass

from src.accounts.models import User

login_manager.login_view = "accounts.login"  # type: ignore[assignment]
login_manager.login_message_category = "danger"

@login_manager.user_loader
def load_user(user_id):
    return User.query.filter(User.id == int(user_id)).first()