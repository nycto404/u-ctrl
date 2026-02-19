#!/bin/sh
set -e

# Default values
: ${PORT:=5001}
: ${WORKERS:=1}
: ${ASYNC:=eventlet}

echo "Starting u-ctrl with async mode=${ASYNC}, workers=${WORKERS}, port=${PORT}"

export SOCKETIO_ASYNC_MODE=${SOCKETIO_ASYNC_MODE:-$ASYNC}

exec gunicorn -k ${ASYNC} -w ${WORKERS} -b 0.0.0.0:${PORT} app.main:app
