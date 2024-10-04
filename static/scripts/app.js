console.log('app.js');

const listSerialPortsButton = document.getElementById('list-serial-ports-button');
const autoConnectButton = document.getElementById('autoconnect-button');
const disconnectButton = document.getElementById('disconnect-button');
const connectButton = document.getElementById('connect-button');
const clearLogButton = document.getElementById('clear-log-button');
const testButton = document.getElementById('test-button');
const monVerButton = document.getElementById('poll-mon-ver-button');
const toggleRxOutputLog = document.getElementById('toggle-rx-output-log');
const serialPortSelect = document.getElementById('serial-port-select');
const baudrateSelect = document.getElementById('baudrate-select');

const lastSuccessfulConnectionDetails = document.getElementById('last-successful-connection-details');

const receiverInfo = document.getElementById('receiver-info');
const monVerTable = document.getElementById('mon-ver-table');
const softwareVersion = document.getElementById('software-version');
const hardwareVersion = document.getElementById('hardware-version');
const extensions = document.getElementById('extensions');

const logs = document.getElementById('logs');

let clientId = sessionStorage.getItem('clientId');

if (!clientId) {
    clientId = Math.random().toString(36).substring(2); // Unique ID
    sessionStorage.setItem('clientId', clientId);
}

let socket = io();

socket.on('connect', function() {
    socket.emit('register_client', {clientId: clientId});
});

// socket.on('disconnect', function() {
//     socket.emit('unregister_client', {clientId: clientId});
// });

let listSerialPorts = () => {
    console.log('listSerialPorts');
    socket.emit('list_serial_ports');
}
socket.on('available_serial_ports', function(data) {
    console.log('Avilable serial ports: ', data);
    console.log('Avilable serial ports: ', typeof(data));
    let newLogEntry = document.createElement('p');
    newLogEntry.textContent = data;
    logs.appendChild(newLogEntry);
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
    logs.appendChild(newLogEntry);
})

let autoConnectReceiver = () => {
    console.log('autoConnectReceiver');
    socket.emit('auto_connect_receiver');
}

socket.on('connection_log', function(data) {
    console.log('Connection log: ', data);
    let newLogEntry = document.createElement('p');
    newLogEntry.textContent = data.serial_port + ", " + data.baudrate + ", " + data.attempt;
    logs.appendChild(newLogEntry);
})

let connectReceiver = () => {
    console.log('connectReceiver');
    let serialPort = serialPortSelect.value;
    let baudrate = baudrateSelect.value;
    if ((serialPort != 'Serial Port') && (baudrate != 'Baudrate')) {
        socket.emit('connect_receiver', {data: 
            {
                'serial_ports': serialPort,
                'baudrate': baudrate
            }
        });
    } else {
        alert("Please select Serial Port & Baudrate!");
    }
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
    console.log('clearLog')
    $('.log-container p').remove();
}

function isRxConnected() {
    console.log('isRxConnected');
    socket.emit('is_rx_connected');
}

socket.on('rx_connection_status', function(data) {
    console.log('rx_connection_status: ', data);
    console.log('rx_connected: ', data['rx_connected']);
    if (data['rx_connected'] == true) {
        $(".connection-status").css({
            "background-color": "#1adb61"
        });
        autoConnectButton.disabled = true;
        connectButton.disabled = true;
        disconnectButton.disabled = false;
        if (!localStorage.getItem('connection_details')) {
            lastSuccessfulConnectionDetails.textContent = data['stream'];
            $('.connection-status').attr('title', data['stream']);
        }
        localStorage.setItem('connection_details', data['stream']);
        monVer();
        setTimeout(logRxOutput, 1500)
    } else {
        $(".connection-status").css({
            "background-color": "#e3103a"
        });
        autoConnectButton.disabled = false;
        connectButton.disabled = false;
        disconnectButton.disabled = true;
    }
})

let monVer = () => {
    console.log("monVer");
    socket.emit('mon_ver');
}

socket.on('mon-ver', function(data) {
    $('#software-version td').remove();
    $('#hardware-version td').remove();
    $('#extensions tr').remove();

    for (info in data['data']) {
        console.log(data['data'][info]);
        if (info == 0) {
            let monVer = document.createElement('td');
            monVer.textContent = data['data'][info];    
            softwareVersion.appendChild(monVer);
        } else if (info == 1) {
            let monVer = document.createElement('td');
            monVer.textContent = data['data'][info];    
            hardwareVersion.appendChild(monVer);
        } else {
            let monVer = document.createElement('tr');
            monVer.textContent = data['data'][info];    
            extensions.appendChild(monVer);
        }
    }
})

let logRxOutput = () => {
    console.log('logRxOutpu9t');
    socket.emit('log_rx_output');
}

socket.on('log_rx_output', function(data) {
    const maxLogLength = 100;
    console.log('log_rx_output');
    console.log(data['data']);
    let newLogEntry = document.createElement('p');
    newLogEntry.textContent = data['data'];
    logs.appendChild(newLogEntry);
    if (logs.children.length >= maxLogLength) {
        logs.removeChild(logs.firstChild);
    }
    logs.scrollTop = logs.scrollHeight;
    console.log('Length of log container: ', logs.children.length)
})

socket.on('nav-pvt', function(data) {
    $('.nav-pvt-data-table td').remove()
    console.log('nav-pvt');
    Object.keys(data['data']).forEach(key => {
        let newEntry = document.createElement('td');
        newEntry.textContent = data['data'][key];
        document.getElementById(key).appendChild(newEntry);
    })
    marker.setLatLng([data['data']['lat'], data['data']['lon']]);
})

listSerialPorts();
isRxConnected();

lastSuccessfulConnectionDetails.textContent = localStorage.getItem('connection_details');
$('.connection-status').attr('title', localStorage.getItem('connection_details'));

listSerialPortsButton.addEventListener("click", listSerialPorts);
autoConnectButton.addEventListener("click", autoConnectReceiver);
disconnectButton.addEventListener("click", disconnectRx);
clearLogButton.addEventListener("click", clearLog);
testButton.addEventListener("click", sendMessage);
connectButton.addEventListener("click", connectReceiver);
monVerButton.addEventListener("click", monVer);