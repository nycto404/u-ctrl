import serial
from pyubx2 import UBXMessage, UBXReader

# Open the serial port
serial_port = serial.Serial('COM7', baudrate=460800, timeout=3)

# Create a UBX message for MON-VER polling (Class 0x0A, ID 0x04)
poll_msg = UBXMessage('MON', 'MON-VER', msgmode=2)

# Send the poll request to the receiver
serial_port.write(poll_msg.serialize())

# Read the response from the receiver
ubx_reader = UBXReader(serial_port)

while True:
    try:
        # Read the incoming UBX message
        (raw_data, parsed_data) = ubx_reader.read()
        
        # If the parsed message is a UBX-MON-VER message, print it
        if parsed_data.identity == 'MON-VER':
            print(f"Software Version Information: {parsed_data}")
            break

    except Exception as e:
        print(f"Error reading UBX message: {e}")
        break

# Close the serial port
serial_port.close()
