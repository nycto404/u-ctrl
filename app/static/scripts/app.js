/*
Code is executed after the page is loaded. Process flow:

1.) listSerialPorts() Client -> list_serial_ports Server; Gets the available serial ports and stores them on the client
2.) isRxConnected(); Client -> is_rx_connected Server; Checks if there is a global variable for the stream

*/
console.log('app.js');

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

if (!localStorage.getItem('is_logging')) {
    localStorage.setItem('is_logging', false);
}

if (!clientId) {
    clientId = Math.random().toString(36).substring(2); // Unique ID
    sessionStorage.setItem('clientId', clientId);
}

let socket = io();

// socket.on('connect', function() {
//     socket.emit('register_client', {clientId: clientId});
// });

// socket.on('disconnect', function() {
//     socket.emit('unregister_client', {clientId: clientId});
// });

socket.on('test', function(data) {
    console.log('Test: ', data);
})

// Request the available serial ports from the server
let listSerialPorts = () => {
    console.log('listSerialPorts');
    socket.emit('list_serial_ports');
}

// Handle the serial ports receiver from the server
socket.on('available_serial_ports', function(data) {
    console.log('Avilable serial ports: ', data);
    console.log('Avilable serial ports: ', typeof(data));
    let newLogEntry = document.createElement('p'); // New log element
    newLogEntry.textContent = data; // Show the serial ports
    logs.appendChild(newLogEntry); // Append element to 'logs' container
    console.log(serialPortSelect.options.length); // How many elements in the dropdown?
    if (serialPortSelect.options.length == 1) { // If there is only the default element ('Serial Port')
        for (let serialPort in data) { //create options for every serial port
            let newSerialPortOption = document.createElement('option');
            newSerialPortOption.value = data[serialPort]; 
            newSerialPortOption.text = data[serialPort];
            serialPortSelect.appendChild(newSerialPortOption); // Append the new element to the 'selects' element
        }
    }
    if (localStorage.getItem('connection_details')) { // If connections details from the last connection have been saved to the localstorage, then call setLatestConnectionInfo()
        setLatestConnectionInfo()
    }
})

// Get latest connection info and populate the dropdown with it
let setLatestConnectionInfo = () => {
    console.log('setLatestConnectionInfo')
    let latestConnectionInfos = localStorage.getItem('connection_details');
    lastSuccessfulConnectionDetails.textContent = latestConnectionInfos;
    console.log(typeof(latestConnectionInfos));
    console.log(latestConnectionInfos);
    if (latestConnectionInfos) {
        const parsedInfo = latestConnectionInfos.match(/port='(.*?)'.*?baudrate=(\d+)/); // Parse connection details string with regex
        const port = parsedInfo[1];
        const baudrate = parsedInfo[2];
        console.log(port, baudrate);
        console.log(serialPortSelect.value);
        console.log(serialPortSelect.options);
        serialPortSelect.value = port;
        baudrateSelect.value = baudrate;
    }
}

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

let isRxConnected = () => {
    console.log('isRxConnected');
    socket.emit('is_rx_connected');
}

socket.on('rx_connection_status', function(data) {
    console.log('rx_connection_status');
    console.log('rx_connection_status: ', data);
    console.log('rx_connected: ', data['rx_connected']);
    if (data['rx_connected'] == true) {
        rxConnected = true;
        $(".connection-status").css({
            "background-color": "#1adb61"
        });
        $('#autoconnect-button').prop('disabled', true);
        $('#connect-button').prop('disabled', true);
        $('#disconnect-button').prop('disabled', false);
        if (!localStorage.getItem('connection_details')) {
            lastSuccessfulConnectionDetails.textContent = data['stream'];
            $('.connection-status').attr('title', data['stream']);
        }
        localStorage.setItem('connection_details', data['stream']);
        if (data['is_logging'] == true) {
            localStorage.setItem('is_logging', true);
        } else {
            localStorage.setItem('is_logging', false);
        }
        monVer();
    } else {
        rxConnected = false;
        $(".connection-status").css({
            "background-color": "#e3103a"
        });
        $('#autoconnect-button').prop('disabled', false);
        $('#connect-button').prop('disabled', false);
        $('#disconnect-button').prop('disabled', true);
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

let enableNavPvt = () => {
    console.log('enableNavPvt');
    socket.emit('enable_nav_pvt');
}

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

let toggleRxOutput = () => {
    console.log('toggleRxOutput');
    if (rxConnected){
        if (localStorage.getItem('is_logging') == 'false') {
            console.log('Rx output will be activated...');
            localStorage.setItem('is_logging', 'true');
            rxLogging = true;
            socket.emit('show_rx_output');
        }   else {
            console.log('Rx output will be deactivated...');
            localStorage.setItem('is_logging', 'false');
            rxLogging = false;
            socket.emit('hide_rx_output');
        }
    } else {
        alert('No receiver connected...');
    }
}



listSerialPorts();
let rxConnected = isRxConnected();


$('.connection-status').attr('title', localStorage.getItem('connection_details'));

$(document).ready(function() {
    $('#list-serial-ports-button').click(function(){
        listSerialPorts();
    });
    $('#autoconnect-button').click(function(){
        autoConnectReceiver();
    });
    $('#connect-button').click(function(){
        connectReceiver();
    });
    $('#disconnect-button').click(function(){
        disconnectRx();
    });
    $('#clear-log-button').click(function(){
        clearLog();
    });
    $('#test-button').click(function(){
        console.log('test')
    });
    $('#poll-mon-ver-button').click(function(){
        monVer();
    });
    $('#enable-nav-pvt-button').click(function(){
        enableNavPvt();
    });
    $('#toggle-rx-output').click(function(){
        toggleRxOutput();
    });

})
