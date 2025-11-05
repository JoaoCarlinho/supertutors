"""Flask extensions initialization."""
from flask_socketio import SocketIO
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

# Initialize extensions
socketio = SocketIO()
cors = CORS()
db = SQLAlchemy()
