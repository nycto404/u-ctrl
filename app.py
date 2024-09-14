from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, send, emit
import lib.ubxlib as ubxlib

stream = None # Initialize data stream variable
rx_connected = False

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

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
    global stream
    print(stream)
    if stream:
        print('Closing stream...')
        stream.close()
        stream = None
        
    is_rx_connected()

@socketio.on('mon_ver')
def mon_ver():
    payload = ubxlib.poll_mon_ver(stream)
    emit('mon-ver', {'data': payload})

@socketio.on('log_rx_output')
def log_rx_output():
    print('log_rx_output')
    ubxlib.log_rx_output(stream, socketio)







@socketio.on('message')
def handle_message(data):
    print('received message: ' + data['data'][0])
    emit('message_response', {'data': 'Message was received by the server!'})

    
if __name__ == '__main__':
    socketio.run(app, debug=True)