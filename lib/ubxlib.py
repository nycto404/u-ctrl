import serial.tools.list_ports, logging, time, traceback
from serial import Serial
from pyubx2 import UBXReader, UBXMessage, UBX_CLASSES, UBX_MSGIDS, NMEA_PROTOCOL, UBX_PROTOCOL
from flask_socketio import SocketIO, emit
import argparse

BAUD_RATES = ["9600", "38400", "115200", "460800", "921600"] # Baudrates to try
MON_VER_MSG = UBXMessage(b'\x0a', b'\x04', 2).serialize() # MON-VER poll hex B5 62 0A 04 00 00 0E 34

coordinates = [] # Empty list for storing lat & lon values

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
                            socketio.emit("connection_log", {
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

                        if "ROM BASE" in str(response) or "$G" in str(response): # 
                            serial_port = port.device
                            #logging.info("UBX message received!")
                            print("Success! Receiver available!")
                            print(f"Serial port: {serial_port}, Baudrate: {baudrate}, Stream: {stream}")
                            if socketio: # Tell the client the great news that there is a connection!!
                                socketio.emit("rx_connected", {
                                    'serial_port': serial_port,
                                    'baudrate': baudrate,
                                    'stream': str(stream),
                                    })
                            return [serial_port, baudrate, stream]
                        else:
                            #logging.warning("No UBX message received... Closing serial connection...")
                            hope = True # Set hope to true if some data is received in the stream
                            print("Closing serial connection...")
                            stream.close()
                    except Exception as e:
                        print(f"Error: {e}")
                        if "Access is denied" in str(e) or "semaphore timeout" in str(e):
                            hope = False # No hope if access denied or semaphore timeout
                            break
                
                if hope == False: # No hope :(, breaking attempts and baudrate iterations until there is hope again...)
                    break

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
        payload.append(parsed_data.extension_07.decode().replace('\x00', ''))
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
        print(parsed_data.extension_07.decode())
        return payload
  










def log_receiver(socketio=None):
    '''Get position and fixtype from NAV-PVT msg'''
    connection_info = auto_connect_receiver()
    try:
        stream = connection_info[2]
        ubr = UBXReader(stream, protfilter=2)
    except Exception as e:
        traceback_str = traceback.format_exc()
        print(traceback_str)

    while True:
        try:
            # Read raw data and parsed data
            (raw_data, parsed_data) = ubr.read()
            # Parse the raw data
            msg = UBXReader.parse(raw_data)
            print(parsed_data)
            # If NAV-PVT msg found, parse lat lon values and write them to the file
            if ("NAV-PVT" in str(msg)):
                print(msg.lat, msg.lon, msg.fixType)
                coordinates.append([msg.lat, msg.lon])
                google_maps_link = "https://www.google.com/maps?q=" + str(msg.lat) + "," + str(msg.lon)
                print(msg, msg.lat, msg.lon, msg.fixType, google_maps_link)
                socketio.emit()
            ###############################################################
        except Exception as e:
            tb = traceback.format_exc()
            print(tb)  

def get_nav_pvt(stream):
    try:
        ubr = UBXReader(stream, protfilter= NMEA_PROTOCOL | UBX_PROTOCOL)
        nav_pvt = UBXMessage(b'NAV', b'PVT', 2)
        print(nav_pvt)

        while True:
            raw_data, parsed_data = ubr.read()
            #print(raw_data)
            #print(parsed_data)
            if "PVT" in str(parsed_data):
                print("\nPVT found!")
                print(parsed_data)
                return parsed_data
        
    
    except Exception as e:
        traceback_str = traceback.format_exc()
        print(traceback_str)

def poll_ubx_msg(msg_class, msg_id):
    # Construct the UBX message
    msg = UBXMessage(msg_class, msg_id, 2)
    print(f'Message: {msg}')

    # Connect to the receiver
    connection_info = auto_connect_receiver()
    stream = connection_info[2]
    ubr = UBXReader(stream)

    output = msg.serialize()
    print(f'Output: {output}')
    stream.write(output)

    time.sleep(0.1)
    response = stream.read(10000)
    print(f'Response: {response}')
    raw_data, parsed_data = ubr.read()

    print(f'Raw Data: {raw_data}')
    print(f'Parsed Data: {parsed_data}')

if __name__ == "__main__":
    #serial_ports = list_available_serial_ports()
    #com_port, baudrate = get_receiver_connection_info(serial_ports)
    #log_receiver(com_port, baudrate)
    #log_receiver()
    #get_nav_pvt()
    poll_ubx_msg("MON", "MON-VER")
