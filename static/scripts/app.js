console.log('app.js');

const listSerialPortsButton = document.getElementById('list-serial-ports-button');
const autoConnectButton = document.getElementById('autoconnect-button');
const disconnectButton = document.getElementById('disconnect-button');
const connectButton = document.getElementById('connect-button');
const clearLogButton = document.getElementById('clear-log-button');
const testButton = document.getElementById('test-button');
const serialPortSelect = document.getElementById('serial-port-select');
const baudrateSelect = document.getElementById('baudrate-select');
const logContainer = document.getElementById('log-container');

let socket = io();

let listSerialPorts = () => {
    console.log('listSerialPorts');
    socket.emit('list_serial_ports');
}
socket.on('available_serial_ports', function(data) {
    console.log('Avilable serial ports: ', data);
    console.log('Avilable serial ports: ', typeof(data));
    let newLogEntry = document.createElement('p');
    newLogEntry.textContent = data;
    logContainer.appendChild(newLogEntry);
    console.log(serialPortSelect.options.length);
    if (serialPortSelect.options.length == 1) {
        for (let serialPort in data) {
            let newSerialPortOption = document.createElement('option');
            newSerialPortOption.value = data[serialPort];
            newSerialPortOption.text = data[serialPort];
            serialPortSelect.appendChild(newSerialPortOption);
        }
    }
})

let sendMessage = () => {
    console.log('sendMessage');
    socket.emit('message', {data: ["Dummy message", "Dummy message no. 2"]});
}
socket.on('message_response', function(data) {
    console.log('Message response: ', data)
    let newLogEntry = document.createElement('p');
    newLogEntry.textContent = data.data;
    logContainer.appendChild(newLogEntry);
})

let autoConnectReceiver = () => {
    console.log('autoConnectReceiver');
    socket.emit('auto_connect_receiver');
}

socket.on('connection_log', function(data) {
    console.log('Connection log: ', data);
    let newLogEntry = document.createElement('p');
    newLogEntry.textContent = data.serial_port + ", " + data.baudrate + ", " + data.attempt;
    logContainer.appendChild(newLogEntry);
})

let connectReceiver = () => {
    console.log('connectReceiver');
    let serialPort = serialPortSelect.value;
    let baudrate = baudrateSelect.value;
    socket.emit('connect_receiver', {data: 
        {
            'serial_ports': serialPort,
            'baudrate': baudrate
        }
    });
}

socket.on('rx_connected', function(data) {
    console.log('Rx connected at: ', data);
    $("#connection-status").text("Connected");
    $(".connection-status").css({
        "background-color": "#1adb61"
    })
})

let disconnectRx = () => {
    console.log("disconnectRx");
    socket.emit('disconnect_rx');
}


let clearLog = () => {
    logContainer.textContent = ""; 
}




let isRxConnected = () => {
    console.log('isRxConnected');
    socket.emit('is_rx_connected');
}

socket.on('rx_connection_status', function(data) {
    console.log('rx_connection_status: ', data);
    if (data == true) {
        $(".connection-status").css({
            "background-color": "#1adb61"
        });
        $("#connection-status").text("Connected");
    } else {
        $(".connection-status").css({
            "background-color": "#e3103a"
        });
        $("#connection-status").text("Disconnected");
    }
})


listSerialPorts();
isRxConnected();

listSerialPortsButton.addEventListener("click", listSerialPorts);
autoConnectButton.addEventListener("click", autoConnectReceiver);
disconnectButton.addEventListener("click", disconnectRx);
clearLogButton.addEventListener("click", clearLog);
testButton.addEventListener("click", sendMessage);
connectButton.addEventListener("click", connectReceiver);