import serial.tools.list_ports

def list_available_ports():
    # Get a list of all available ports
    ports = serial.tools.list_ports.comports()
    
    if ports:
        print("Available COM Ports:")
        for port in ports:
            print(port.device)
    else:
        print("No COM Ports available.")
    
    return ports

if __name__ == "__main__":
    list_available_ports()
