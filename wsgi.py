from app.main import app, socketio  # Import your Flask app object

if __name__ == "__main__":
    socketio.run(app)  # For testing, not used with Gunicorn
