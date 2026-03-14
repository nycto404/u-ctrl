from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, send, emit
import logging
import os

try:
    # Works when starting from repository root (e.g. `python -m app.main`).
    from app.library import ubxlib
    from app.server_state import ServerState
except ModuleNotFoundError:
    # Works when running as a script from within the app directory/container entrypoint.
    from library import ubxlib
    from server_state import ServerState


logging.basicConfig(level=logging.INFO)

state = ServerState()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
# Allow overriding async mode via environment variable for Docker/runtime flexibility.
# If not set, Flask-SocketIO will choose the best available async mode (eventlet/gevent/threading).
async_mode = os.environ.get('SOCKETIO_ASYNC_MODE', None)
cors_allowed_origins = os.environ.get('SOCKETIO_CORS_ALLOWED_ORIGINS', None)
if cors_allowed_origins and ',' in cors_allowed_origins:
    cors_allowed_origins = [origin.strip() for origin in cors_allowed_origins.split(',') if origin.strip()]
socketio = SocketIO(app, async_mode=async_mode, cors_allowed_origins=cors_allowed_origins)


def is_running_in_docker():
    """Best-effort detection for Docker/containerized execution."""
    if os.path.exists('/.dockerenv'):
        return True
    try:
        with open('/proc/1/cgroup', 'r', encoding='utf-8') as cgroup_file:
            cgroup = cgroup_file.read()
        return any(marker in cgroup for marker in ('docker', 'containerd', 'kubepods'))
    except OSError:
        return False


@app.context_processor
def inject_runtime_info():
    """Expose runtime environment label to all templates."""
    running_in_docker = is_running_in_docker()
    frontend_dev_server_url = os.environ.get('FRONTEND_DEV_SERVER_URL', '').rstrip('/')
    return {
        'running_in_docker': running_in_docker,
        'runtime_environment': 'Docker' if running_in_docker else 'Local',
        'frontend_dev_server_url': frontend_dev_server_url
    }

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@socketio.on('register_client')
def register_client(data):
    client_id = data['clientId']
    sid = request.sid
    logging.info('client_id %s connected with sid %s', client_id, sid)

    state.clients[client_id] = sid
    logging.debug('clients: %s', state.clients)

@socketio.on('disconnect')
def unregister_client():
    logging.info('unregister_client')
    #clients.pop(data['client_id'])
    #print(clients)


@socketio.on('list_serial_ports')
def list_serial_ports():
    ports = ubxlib.list_available_serial_ports()
    if isinstance(ports, list) and len(ports) > 1:
        emit('available_serial_ports', ports[1])
    else:
        emit('available_serial_ports', [])

@socketio.on('auto_connect_receiver')
def auto_connect_receiver():
    connection_info = ubxlib.auto_connect_receiver(socketio)
    logging.info('auto_connect_receiver: %s', connection_info)
    if connection_info:
        state.stream = connection_info[2]
    is_rx_connected()

@socketio.on('connect_receiver')
def connect(data):
    serial_port = data['data']['serial_ports']
    baudrate = data['data']['baudrate']
    connection_info = ubxlib.connect_receiver(serial_port, baudrate, socketio)
    logging.info('connect: %s', connection_info)
    if connection_info:
        state.stream = connection_info[2]
    is_rx_connected()

@socketio.on('is_rx_connected')
def is_rx_connected():
    logging.debug('is_rx_connected')
    logging.debug('stream: %s', state.stream)
    state.rx_connected = bool(state.stream)
    emit('rx_connection_status', {
                                'rx_connected': state.rx_connected,
                                'stream': str(state.stream),
                                'is_logging': state.is_logging
                                })    
                                
@socketio.on('disconnect_rx')
def disconnect_rx():
    logging.info('disconnect_rx')
    hide_rx_output()
    logging.debug('Stream before closing: %s', state.stream)
    if state.stream:
        logging.info('Closing stream...')
        try:
            state.stream.close()
        except Exception:
            logging.exception('Error closing stream')
        state.stream = None
        state.rx_connected = False
        logging.debug('Stream after closing: %s', state.stream)
    is_rx_connected()

@socketio.on('mon_ver')
def mon_ver():
    logging.info('mon_ver')
    if not state.is_logging and state.stream:
        payload = ubxlib.poll_mon_ver(state.stream, socketio)
        emit('mon-ver', {'data': payload})

@socketio.on('show_rx_output')
def show_rx_output():
    logging.info('show_rx_output')
    if not state.is_logging and state.stream:
        state.is_logging = True
        # Start background task that reads from stream and emits via socketio
        socketio.start_background_task(ubxlib.log_rx_output, state.stream, socketio, lambda: state.is_logging)

@socketio.on('hide_rx_output')
def hide_rx_output():
    logging.info('hide_rx_output')
    if state.is_logging:
        state.is_logging = False
    is_rx_connected()

@socketio.on('enable_nav_pvt')
def enable_nav_pvt():
    ubxlib.enable_nav_pvt_message(state.stream, socketio)
    logging.info('enable_nav_pvt')

@socketio.on('enable_useful_msgs')
def enable_useful_msgs():
    ubxlib.enable_useful_msgs(state.stream, socketio)
    logging.info('enable_useful_msgs')


@socketio.on('message')
def handle_message(data):
    logging.info('received message: %s', data.get('data'))
    emit('message_response', {'data': 'Message was received by the server!'})

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0')