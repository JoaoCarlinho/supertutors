"""Flask application entry point."""
from app import create_app
from app.extensions import socketio, db

app = create_app()

# Initialize database tables
with app.app_context():
    db.create_all()
    app.logger.info("Database tables created successfully")

if __name__ == '__main__':
    import os
    # Use port 5000 inside container (Docker maps to 5001 externally)
    port = int(os.getenv('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
