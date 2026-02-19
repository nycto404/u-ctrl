import serial.tools.list_ports
import logging
import time
import traceback
from serial import Serial
from pyubx2 import UBXReader, UBXMessage, NMEA_PROTOCOL, UBX_PROTOCOL, SET_LAYER_RAM, SET_LAYER_FLASH, SET_LAYER_BBR, TXN_NONE
from flask_socketio import SocketIO, emit
import argparse
import threading
from typing import List, Optional, Tuple, Callable, Any


LOG = logging.getLogger(__name__)
LOG.addHandler(logging.NullHandler())

BAUD_RATES = ["9600", "38400", "115200", "460800", "921600"]
MON_VER_MSG = UBXMessage(b'\x0a', b'\x04', 2).serialize()
USEFUL_MSGS = [
    "ESF_MEAS", "ESF_STATUS", "MON_COMMS", "MON_HW", "MON_HW3",
    "MON_IO", "MON_MSGPP", "MON_RF", "MON_RXBUF", "MON_SPAN",
    "MON_SYS", "MON_TEMP", "MON_TXBUF", "NAV_PVT", "NAV_SAT",
    "NAV_SBAS", "NAV_SIG", "RXM_COR",
]

# Get a list of serial ports available on the system 
def list_available_serial_ports():
    ''' Get available serial ports '''
    try:
        # Get a list of all available ports
        ports = serial.tools.list_ports.comports()
        serial_ports: List[str] = []

        if ports:
            LOG.info("Available COM Ports: %s", [p.device for p in ports])
            for port in ports:
                serial_ports.append(port.device)
            return [ports, serial_ports]
        else:
            LOG.info("No COM Ports available.")
            return [[], []]
    except Exception as e:
        LOG.exception("Error listing serial ports")
        return [[], []]
    
def auto_connect_receiver(socketio=None):
    '''
    Try the found serial ports with different baudrates by polling the MON-VER UBX message and check if "ROM BASE" is in th reply.
    Also listening for any '$G' (beginning of NMEA protocol) in the stream.
    '''
    hope = False
    try:
        ports = list_available_serial_ports()
        LOG.info("Trying to connect to receiver...")
        for port in ports[0]:
            if ("Bluetooth" in getattr(port, 'description', '')):
                continue
            for baudrate in BAUD_RATES:
                LOG.debug("Trying %s at %s", port.device, baudrate)
                for attempt in range(3):
                    LOG.debug("Attempt: %d", attempt + 1)
                    try:
                        if socketio:
                            socketio.emit("connection_log", {
                                'serial_port': port.device,
                                'baudrate': baudrate,
                                'attempt': attempt + 1
                            })
                            time.sleep(0)
                        stream = Serial(port.device, timeout=0.5, baudrate=baudrate)
                        time.sleep(0.5)
                        stream.write(MON_VER_MSG)
                        time.sleep(0.1)
                        response = stream.read(1024)
                        LOG.debug("Response: %s", response)

                        if "ROM BASE" in str(response) or "$G" in str(response):
                            serial_port = port.device
                            LOG.info("Success! Receiver available: %s %s", serial_port, baudrate)
                            if socketio:
                                socketio.emit("rx_connected", {
                                    'serial_port': serial_port,
                                    'baudrate': baudrate,
                                    'stream': str(stream)
                                })
                                time.sleep(0)
                            return [serial_port, baudrate, stream]
                        elif (len(response) <= 1):
                            LOG.debug("No data... Skipping...")
                            stream.close()
                            time.sleep(0.25)
                            break
                        else:
                            hope = True
                            LOG.debug("Only garbage received... Closing serial connection...")
                            stream.close()
                            time.sleep(0.25)
                    except Exception as e:
                        LOG.exception("Error during auto_connect attempt")
                        if "Access is denied" in str(e) or "semaphore timeout" in str(e):
                            hope = False
                            break
                if hope is False:
                    break
        LOG.info("No receiver detected...")
    except Exception:
        tb = traceback.format_exc()
        LOG.exception("An exception occured in auto_connect_receiver: %s", tb)
    return None

def connect_receiver(serial_port, baudrate, socketio=None):
    try:
        for attempt in range (3): # Try several times
            LOG.debug('Connection attempt no.: %s', attempt)
            stream = Serial(serial_port, timeout=1, baudrate=baudrate)
            stream.write(MON_VER_MSG)
            time.sleep(0.1)
            response = stream.read(4096)
            LOG.debug('Response: %s', response)
            if "ROM BASE" in str(response) or "$G" in str(response):
                LOG.info('Success! Receiver available: %s %s', serial_port, baudrate)
                if socketio:
                    socketio.emit("rx_connected", {
                        'serial_port': serial_port,
                        'baudrate': baudrate,
                        'stream': str(stream),
                        })
                    time.sleep(0)
                return [serial_port, baudrate, stream]
            else:
                stream.close()
                time.sleep(0.25)

    except Exception as e:
        LOG.exception('Error connecting to receiver: %s', e)
        if "Access is denied" in str(e) or "semaphore timeout" in str(e):
            return None

def poll_mon_ver(stream, socketio=None):
    payload: List[str] = []
    try:
        ubr = UBXReader(stream, protfilter=NMEA_PROTOCOL | UBX_PROTOCOL)
        while True:
            stream.write(MON_VER_MSG)
            raw_data, parsed_data = ubr.read()
            if 'MON-VER' in str(parsed_data) or getattr(parsed_data, 'identity', '') == 'MON-VER':
                for fld in ('swVersion', 'hwVersion', 'extension_01', 'extension_02', 'extension_03', 'extension_04', 'extension_05', 'extension_06'):
                    val = getattr(parsed_data, fld, b'')
                    try:
                        payload.append(val.decode().replace('\x00', ''))
                    except Exception:
                        payload.append(str(val))
                LOG.debug('MON-VER payload: %s', payload)
                if socketio:
                    socketio.emit('log_rx_output', { 'data': payload })
                    time.sleep(0)
                return payload
    except Exception:
        LOG.exception('Error polling MON-VER')
    return []
  
def log_rx_output(stream, socketio = None, is_logging = None):
    LOG.info('ubxlib.log_rx_output started')
    LOG.debug('Stream: %s socketio: %s', stream, socketio)
    ubr = UBXReader(stream, protfilter=NMEA_PROTOCOL | UBX_PROTOCOL)
    while is_logging() if callable(is_logging) else True:
        try:
            raw_data, parsed_data = ubr.read()
            LOG.debug('raw: %s parsed: %s', raw_data, parsed_data)

            if 'PVT' in str(parsed_data) or getattr(parsed_data, 'identity', '') == 'NAV-PVT':
                pvt_data = {
                    'iTOW': getattr(parsed_data, 'iTOW', None),
                    'year': getattr(parsed_data, 'year', None),
                    'month': getattr(parsed_data, 'month', None),
                    'day': getattr(parsed_data, 'day', None),
                    'fix_type': getattr(parsed_data, 'fixType', None),
                    'lat': getattr(parsed_data, 'lat', None),
                    'lon': getattr(parsed_data, 'lon', None),
                    'height': getattr(parsed_data, 'height', None),
                    'speed': getattr(parsed_data, 'gSpeed', None),
                }
                LOG.debug('NAV-PVT data: %s', pvt_data)
                if socketio:
                    LOG.debug('Emitting NAV-PVT data')
                    socketio.emit('nav-pvt', {'data': pvt_data})
                    socketio.sleep(0)

            if socketio:
                socketio.emit('log_rx_output', {'data': str(parsed_data)})
                socketio.sleep(0)

        except Exception:
            LOG.exception('Error reading from stream')
            break

def enable_nav_pvt_message(stream, socketio = None):
    LAYERS = [SET_LAYER_RAM, SET_LAYER_BBR, SET_LAYER_FLASH]
    INTERFACES = ["UART1", "UART2", "USB"]
    transaction = TXN_NONE
    try:
        for layer in LAYERS:
            for interface in INTERFACES:
                cfgData = [(f"CFG_MSGOUT_UBX_NAV_PVT_{interface}", 1)]
                msg = UBXMessage.config_set(layer, transaction, cfgData)
                if socketio:
                    socketio.emit("log_rx_output", {'data': str(msg)})
                    time.sleep(0)
                LOG.debug('Writing message: %s', msg)
                stream.write(msg.serialize())
    except Exception:
        tb = traceback.format_exc()
        LOG.exception('Something went wrong enabling NAV-PVT: %s', tb)
        if socketio:
            socketio.emit('log_rx_output', {'data': str(tb)})
            time.sleep(0)

def enable_useful_msgs(stream, socketio=None):
    LAYERS = [SET_LAYER_RAM, SET_LAYER_BBR, SET_LAYER_FLASH]
    INTERFACES = ["UART1", "UART2", "USB"]
    transaction = TXN_NONE
    try:
        for layer in LAYERS:
            for msg_name in USEFUL_MSGS:
                LOG.debug('Enabling %s', msg_name)
                for interface in INTERFACES:
                    cfgData = [(f"CFG_MSGOUT_UBX_{msg_name}_{interface}", 1)]
                    msg = UBXMessage.config_set(layer, transaction, cfgData)
                    if socketio:
                        socketio.emit('log_rx_output', {'data': str(msg)})
                        time.sleep(0)
                    LOG.debug('Writing message: %s', msg)
                    stream.write(msg.serialize())
    except Exception:
        tb = traceback.format_exc()
        LOG.exception('Something went wrong enabling useful messages: %s', tb)
        if socketio:
            socketio.emit('log_rx_output', {'data': str(tb)})
            time.sleep(0)



if __name__ == "__main__":
    print('Script only execution')
    stream = auto_connect_receiver()[2]
    log_rx_output(stream)
    #enable_nav_pvt_message(stream)
