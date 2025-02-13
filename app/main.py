from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, send, emit
import library.ubxlib as ubxlib
# from eventlet import wsgi
import uuid

stream = None # Initialize data stream variable
clients = {}
rx_connected = False # 
is_logging = False # To avoid creating several UBXReader instances when rx_logging is triggere, not a good solution though

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
def unregister_client(data):
    print('unregister_client')
    clients.pop(data['client_id'])
    print(clients)


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
    global stream, rx_connected
    if stream:
        rx_connected = True
    else:
        rx_connected = False
    emit('rx_connection_status', {
                                'rx_connected': rx_connected,
                                'stream': str(stream)
                                })
                                
@socketio.on('disconnect_rx')
def disconnect_rx():
    print('disconnect_rx')
    global stream, is_logging
    print(stream)
    if stream:
        print('Closing stream...')
        stream.close()
        stream = None
        is_logging = False
    is_rx_connected()

@socketio.on('mon_ver')
def mon_ver():
    print('mon_ver')
    global is_logging
    if is_logging == False:
        payload = ubxlib.poll_mon_ver(stream)
        emit('mon-ver', {'data': payload})

@socketio.on('log_rx_output')
def log_rx_output():
    global is_logging
    if is_logging == False:
        print('log_rx_output')
        is_logging = True
        ubxlib.log_rx_output(stream, socketio)

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
    # import eventlet # type: ignore
    # wsgi.server(eventlet.listen(("0.0.0.0", 5001)), app)
    socketio.run(app, debug=True)