import serial.tools.list_ports, logging, time, traceback
from serial import Serial
from pyubx2 import UBXReader, UBXMessage, NMEA_PROTOCOL, UBX_PROTOCOL, SET_LAYER_RAM, SET_LAYER_FLASH, SET_LAYER_BBR, TXN_NONE
from flask_socketio import SocketIO, emit
import argparse

BAUD_RATES = ["9600", "38400", "115200", "460800", "921600"] # Baudrates to try
MON_VER_MSG = UBXMessage(b'\x0a', b'\x04', 2).serialize() # MON-VER poll hex B5 62 0A 04 00 00 0E 34

coordinates = [] # Empty list for storing lat & lon values

def emit_msg(socket, event, data):
    try:
        socket.emit(event, data)
    except Exception as e:
        print(f"Something went wrong: {e}")

# Get a list of serial ports available on the system 
def list_available_serial_ports():
    ''' Get available serial ports '''
    try:
        # Get a list of all available ports
        ports = serial.tools.list_ports.comports()
        serial_ports = []

        if ports:
            print("Available COM Ports:")
            for port in ports:
                print(port.device)
                serial_ports.append(port.device)
            return [ports, serial_ports]
        else:
            print("No COM Ports available.")
            return "No COM ports available..."
    except Exception as e:
        print(e)
        return str(e)
    


def auto_connect_receiver(socketio=None):
    '''
    Try the found serial ports with different baudrates by polling the MON-VER UBX message and check if "ROM BASE" is in th reply.
    Also listening for any '$G' (beginning of NMEA protocol) in the stream.
    '''
    
    hope = False # Variable to determine if it worth to do further conenction and listening attempts. I.e. if access is denied, no hope to try other baudrates...

    try:
        # Getting the available serial ports
        ports = list_available_serial_ports()
        #logging.basicConfig(filename='receiver_logs/' + timestamp + '.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
        #logging.info("Trying to connect to UBX receiver...")
        print("Trying to connect to receiver...")
        for port in ports[0]: # Loop through serial ports
            for baudrate in BAUD_RATES: # Loop through baudrates
                #logging.info(port.device + " at " + baudrate)
                print(port.device + " at " + baudrate)
                for attempt in range(3): # Trying 3 times
                    #logging.info("Attempt: " + str(attempt+1))
                    print("Attempt: " + str(attempt+1))
                    try:
                        if socketio: # Send logs to the client if there is an open socket
                            emit_msg(socketio, "connection_log", {
                                'serial_port': port.device,
                                'baudrate': baudrate,
                                'attempt': attempt+1
                            })
                        stream = Serial(port.device, timeout=0.5, baudrate=baudrate) # Opening serial conn.
                        #logging.info("Sending MON-VER: " + str(MON_VER_MSG))
                        stream.write(MON_VER_MSG) # Sending the MON-VER msg to the stream
                        time.sleep(0.1)
                        response = stream.read(1024) # Read 1024 bytes from the stream
                        print(str(response))
                        #logging.info("Response: " + str(response))

                        # Either UBX or NMEA message has been received
                        if "ROM BASE" in str(response) or "$G" in str(response): # 
                            serial_port = port.device
                            #logging.info("UBX message received!")
                            print("Success! Receiver available!")
                            print(f"Serial port: {serial_port}, Baudrate: {baudrate}, Stream: {stream}")
                            if socketio: # Tell the client the great news that there is a connection!!
                                emit_msg(socketio, "rx_connected", {
                                    'serial_port': serial_port,
                                    'baudrate': baudrate,
                                    'stream': str(stream),
                                    })
                            return [serial_port, baudrate, stream]
                        
                        # If received data length is less or equal one byte, abort the attempt
                        elif (len(response) <= 1):
                            print("No data... Skipping...")
                            stream.close()
                            time.sleep(0.25) # Wait a bit after closing
                            break

                        else:
                            #logging.warning("No UBX message received... Closing serial connection...")
                            hope = True # Set hope to true if some data is received in the stream
                            print("Only garbage received... Closing serial connection...")
                            stream.close()
                            time.sleep(0.25) # Wait a bit after closing
                            
                    except Exception as e:
                        print(f"Error: {e}")
                        if "Access is denied" in str(e) or "semaphore timeout" in str(e):
                            hope = False # No hope if access denied or semaphore timeout
                            break
                
                if hope == False: # No hope :(, breaking attempts and baudrate iterations until there is hope again...)
                    break
        print("No receiver detected...")

    except Exception as e:            
        tb = traceback.format_exc()
        #logging.critical("An exception occured")
        #logging.critical(f"Error: {e}")
        #logging.critical("Traceback details:")
        #logging.critical(tb)
        print("An exception occured")
        print(f"Error: {e}")
        print("Traceback details:")
        print(tb)
        print(f"Error: {e}")

def connect_receiver(serial_port, baudrate, socketio=None):
    try:
        for attempt in range (3): # Try several times
            print(f'Connection attempt no.: {attempt}')
            stream = Serial(serial_port, timeout=1, baudrate=baudrate)
            stream.write(MON_VER_MSG) # Sending the MON-VER msg to the stream
            time.sleep(0.1)
            response = stream.read(4096) # Read 2048 bytes from the stream
            print(str(response))
            if "ROM BASE" in str(response) or "$G" in str(response):
                serial_port = serial_port
                print("Success! Receiver available!")
                print(f"Serial port: {serial_port}, Baudrate: {baudrate}, Stream: {stream}")
                if socketio:
                    socketio.emit("rx_connected", {
                        'serial_port': serial_port,
                        'baudrate': baudrate,
                        'stream': str(stream),
                        })
                return [serial_port, baudrate, stream]
            else:
                stream.close()
                time.sleep(0.25) # Wait a bit after closing

    except Exception as e:
        print(f"Error: {e}")
        if "Access is denied" in str(e) or "semaphore timeout" in str(e):
            return

def poll_mon_ver(stream):
    payload = []
    ubr = UBXReader(stream, protfilter=NMEA_PROTOCOL | UBX_PROTOCOL)
    while True:
      stream.write(MON_VER_MSG)
      raw_data, parsed_data = ubr.read()
      if 'MON-VER' in str(parsed_data):
        payload.append(parsed_data.swVersion.decode().replace('\x00', ''))
        payload.append(parsed_data.hwVersion.decode().replace('\x00', ''))
        payload.append(parsed_data.extension_01.decode().replace('\x00', ''))
        payload.append(parsed_data.extension_02.decode().replace('\x00', ''))
        payload.append(parsed_data.extension_03.decode().replace('\x00', ''))
        payload.append(parsed_data.extension_04.decode().replace('\x00', ''))
        payload.append(parsed_data.extension_05.decode().replace('\x00', ''))
        payload.append(parsed_data.extension_06.decode().replace('\x00', ''))
        #payload.append(parsed_data.extension_07.decode().replace('\x00', ''))
        print(payload)
        print(type(parsed_data))
        print(parsed_data)
        print(parsed_data.swVersion.decode())
        print(parsed_data.hwVersion.decode())
        print(parsed_data.extension_01.decode())
        print(parsed_data.extension_02.decode())
        print(parsed_data.extension_03.decode())
        print(parsed_data.extension_04.decode())
        print(parsed_data.extension_05.decode())
        print(parsed_data.extension_06.decode())
        #print(parsed_data.extension_07.decode())
        return payload
  
def log_rx_output(stream, socketio = None):
    ubr = UBXReader(stream, protfilter=NMEA_PROTOCOL | UBX_PROTOCOL)
    while stream:
        raw_data, parsed_data = ubr.read()
        print(raw_data)
        print(parsed_data)

        # IF NAV-PVT is found, create dictionary for easy handling on client side
        if 'PVT' in str(parsed_data):
            pvt_data = {
                        'iTOW': parsed_data.iTOW,
                        'year': parsed_data.year,
                        'month': parsed_data.month,
                        'day': parsed_data.day,
                        'fix_type': parsed_data.fixType,
                        'lat': parsed_data.lat,
                        'lon': parsed_data.lon,
                        'height': parsed_data.height,
                        'speed': parsed_data.gSpeed
            }
            print(f'NAV-PVT data: {pvt_data}')
            if socketio:
                socketio.emit('nav-pvt', {'data': pvt_data})            

        if socketio:
            socketio.emit('log_rx_output', {'data': str(parsed_data)})

def enable_nav_pvt_message(stream, socketio = None):
    LAYERS = [SET_LAYER_RAM, SET_LAYER_BBR, SET_LAYER_FLASH]
    INTERFACES = ["UART1", "UART2", "USB"]
    transaction = TXN_NONE
    cfgData = [("CFG_MSGOUT_UBX_NAV_PVT_USB", 1)]
    try:
        # For every layer    
        for layer in LAYERS:
            # For each interface
            for interface in INTERFACES:
                cfgData = [(f"CFG_MSGOUT_UBX_NAV_PVT_{interface}", 1)]
                msg = UBXMessage.config_set(layer, transaction, cfgData)
                if socketio:
                    emit_msg(socketio, log_rx_output, msg)
                print(msg)
                stream.write(msg.serialize())
    except Exception as e:
        tb = traceback.format_exc()
        print(f"Something went wrong: {e}")
        print(tb)
        if socketio:
            emit_msg(socketio, log_rx_output, tb)


if __name__ == "__main__":
    print('Script only execution')
    stream = auto_connect_receiver()[2]
    #log_rx_output(stream)
    enable_nav_pvt_message(stream)
