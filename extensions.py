from flask_socketio import SocketIO

# Initialize SocketIO without app first
# This avoids circular imports when routes need to import socketio
# using threading mode for better Windows compatibility
socketio = SocketIO(cors_allowed_origins="*", async_mode='threading')
