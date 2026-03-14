# Build frontend assets with Vite
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

COPY frontend /app/frontend
RUN npm run build


# Use a lightweight Python image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install build dependencies and system packages needed by some Python deps
RUN apt-get update && apt-get install -y --no-install-recommends \
	build-essential \
	&& rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files to the container
COPY . /app

# Copy compiled frontend assets from the Node build stage
COPY --from=frontend-builder /app/app/static/dist /app/app/static/dist

# Ensure entrypoint is executable
RUN chmod +x /app/entrypoint.sh || true

# Use environment variable to allow choosing async mode at runtime
ENV SOCKETIO_ASYNC_MODE=eventlet

# Expose the application's port
EXPOSE 5001

# Default entrypoint runs gunicorn with configured options
ENTRYPOINT ["/app/entrypoint.sh"]
