from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config
from models import db, User
from routes import auth_bp, chat_bp, home_bp
from events import register_chat_events
from extensions import socketio

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
socketio.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login."""
    return User.query.get(int(user_id))


# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(home_bp)

# Register SocketIO events
register_chat_events(socketio)


# Create database tables
with app.app_context():
    db.create_all()


if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
