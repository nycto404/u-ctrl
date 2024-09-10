console.log('app.js');

const listSerialPortsButton = document.getElementById('list-serial-ports-button');
const autoConnectButton = document.getElementById('autoconnect-button');
const clearLogButton = document.getElementById('clear-log-button');
const testButton = document.getElementById('test-button');
const logContainer = document.getElementById('log-container');

let socket = io();

let listSerialPorts = () => {
    console.log('listSerialPorts');
    socket.emit('list_serial_ports');
}
socket.on('available_serial_ports', function(data) {
    console.log('Avilable serial ports: ', data);
    let newLogEntry = document.createElement('p');
    newLogEntry.textContent = data;
    logContainer.appendChild(newLogEntry);
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

let autoConnect = () => {
    console.log('autoConnect');
    socket.emit('auto_connect_receiver');
}

socket.on('connection_log', function(data) {
    console.log('Connection log: ', data);
    let newLogEntry = document.createElement('p');
    newLogEntry.textContent = data.serial_port + ", " + data.baudrate + ", " + data.attempt;
    logContainer.appendChild(newLogEntry);
})

socket.on('rx_connected', function(data) {
    console.log('Rx connected at: ', data);
    

})

let clearLog = () => {
    logContainer.textContent = ""; 
}

listSerialPortsButton.addEventListener("click", listSerialPorts);
autoConnectButton.addEventListener("click", autoConnect);
clearLogButton.addEventListener("click", clearLog);
testButton.addEventListener("click", sendMessage);