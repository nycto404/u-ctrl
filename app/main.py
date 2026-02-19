from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, send, emit
from app.library import ubxlib
from app.server_state import ServerState
import logging
import os


logging.basicConfig(level=logging.INFO)

state = ServerState()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
# Allow overriding async mode via environment variable for Docker/runtime flexibility.
# If not set, Flask-SocketIO will choose the best available async mode (eventlet/gevent/threading).
async_mode = os.environ.get('SOCKETIO_ASYNC_MODE', None)
socketio = SocketIO(app, async_mode=async_mode)

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
    socketio.run(app, debug=True)