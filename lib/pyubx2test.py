from serial import Serial
from pyubx2 import UBXReader, UBXMessage, NMEA_PROTOCOL, UBX_PROTOCOL

MON_VER_MSG = UBXMessage(b'\x0a', b'\x04', 2).serialize() # MON-VER poll hex B5 62 0A 04 00 00 0E 34

with Serial('COM26', 38400, timeout=3) as stream:
    ubr = UBXReader(stream)
    while True:
        stream.write(MON_VER_MSG)
        raw_data, parsed_data = ubr.read()
        if parsed_data is not None:
                print(parsed_data)