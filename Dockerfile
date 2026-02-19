# Use a lightweight Python image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install build dependencies and system packages needed by some Python deps
RUN apt-get update && apt-get install -y --no-install-recommends \
	build-essential \
	&& rm -rf /var/lib/apt/lists/*

# Copy application files to the container
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Use environment variable to allow choosing async mode at runtime
ENV SOCKETIO_ASYNC_MODE=eventlet

# Expose the application's port
EXPOSE 5001

# Start the app with Gunicorn using eventlet worker suitable for SocketIO
CMD ["gunicorn", "-k", "eventlet", "-w", "1", "-b", "0.0.0.0:5001", "app.main:app"]
