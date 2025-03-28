from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, send, emit
import library.ubxlib as ubxlib
# from eventlet import wsgi
import uuid
import threading

stream = None # Initialize data stream variable
clients = {}
rx_connected = False # 
is_logging = False # To avoid creating several UBXReader instances when rx_logging is triggere, not a good solution though
logging_thread = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

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
    print(f'cliend_id {client_id} connected with sid {sid}')
    
    clients[client_id] = sid
    print(clients)

@socketio.on('disconnect')
def unregister_client():
    print('unregister_client')
    #clients.pop(data['client_id'])
    #print(clients)


@socketio.on('list_serial_ports')
def list_serial_ports():
    ports = ubxlib.list_available_serial_ports()
    emit('available_serial_ports', ports[1])

@socketio.on('auto_connect_receiver')
def auto_connect_receiver():
    global stream
    connection_info = ubxlib.auto_connect_receiver(socketio)
    print(connection_info)
    stream = connection_info[2]
    is_rx_connected()

@socketio.on('connect_receiver')
def connect(data):
    global stream
    serial_port = data['data']['serial_ports']
    baudrate = data['data']['baudrate']
    connection_info = ubxlib.connect_receiver(serial_port, baudrate, socketio)
    print(connection_info)
    stream = connection_info[2]
    is_rx_connected()

@socketio.on('is_rx_connected')
def is_rx_connected():
    print('is_rx_connected')
    global stream, rx_connected, is_logging
    print(stream)
    if stream:
        rx_connected = True
    else:
        rx_connected = False
    emit('rx_connection_status', {
                                'rx_connected': rx_connected,
                                'stream': str(stream),
                                'is_logging': is_logging
                                })    
                                
@socketio.on('disconnect_rx')
def disconnect_rx():
    print('disconnect_rx')
    global stream, rx_connected
    hide_rx_output()
    print(f"Stream before closing: {stream}")
    if stream:
        print('Closing stream...')
        stream.close()
        stream = None
        rx_connected = False
        print(f"Stream after closing: {stream}")
    is_rx_connected()  # Ensure rx_connection_status is emitted after disconnecting

@socketio.on('mon_ver')
def mon_ver():
    print('mon_ver')
    global is_logging
    if is_logging == False:
        payload = ubxlib.poll_mon_ver(stream, socketio)
        emit('mon-ver', {'data': payload})

@socketio.on('show_rx_output')
def show_rx_output():
    print('show_rx_output')
    global logging_thread, is_logging
    if not is_logging:
        is_logging = True
        socketio.start_background_task(target=ubxlib.log_rx_output, stream=stream, socketio=socketio, is_logging=lambda: is_logging)

@socketio.on('hide_rx_output')
def hide_rx_output():
    print('hide_rx_output')
    global logging_thread, is_logging
    if is_logging:
        is_logging = False
    is_rx_connected()  # Add this line to emit the rx_connection_status event

@socketio.on('enable_nav_pvt')
def enable_nav_pvt():
    global stream
    ubxlib.enable_nav_pvt_message(stream, socketio)
    print('enable_nav_pvt')

@socketio.on('message')
def handle_message(data):
    print('received message: ' + data['data'][0])
    emit('message_response', {'data': 'Message was received by the server!'})

if __name__ == '__main__':
    socketio.run(app, debug=True)