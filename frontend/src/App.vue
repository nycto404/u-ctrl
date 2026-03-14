<script setup>
import { nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue';
import ControlPanel from './components/ControlPanel.vue';
import TelemetryPanel from './components/TelemetryPanel.vue';
import LogPanel from './components/LogPanel.vue';
import { NAV_PVT_FIELDS } from './constants/telemetryFields';
import { useLeafletMap } from './composables/useLeafletMap';
import { createSocketClient } from './services/socketClient';

const baudrates = [9600, 38400, 115200, 460800, 921600];
const serialPorts = ref([]);
const selectedSerialPort = ref('');
const selectedBaudrate = ref('');
const rxConnected = ref(false);
const isLogging = ref(localStorage.getItem('is_logging') === 'true');
const logs = ref([]);
const navPvt = reactive({});
const monVerData = reactive({
    softwareVersion: '',
    hardwareVersion: '',
    extensions: []
});
const lastSuccessfulConnection = ref(localStorage.getItem('connection_details') || '');

let socket = null;

const { mapElement, initMap, setMarkerPosition, destroyMap } = useLeafletMap();

const appendLog = (entry) => {
    if (!entry && entry !== 0) {
        return;
    }

    logs.value.push(String(entry));
    if (logs.value.length > 100) {
        logs.value.shift();
    }

    nextTick(() => {
        const logContainer = document.getElementById('logs');
        if (logContainer) {
            logContainer.scrollTop = logContainer.scrollHeight;
        }
    });
};

const tryLoadLatestConnection = () => {
    if (!lastSuccessfulConnection.value) {
        return;
    }

    const parsedInfo = lastSuccessfulConnection.value.match(/port='(.*?)'.*?baudrate=(\d+)/);
    if (!parsedInfo) {
        return;
    }

    const savedPort = parsedInfo[1];
    const savedBaudrate = parsedInfo[2];
    if (serialPorts.value.includes(savedPort)) {
        selectedSerialPort.value = savedPort;
    }
    if (baudrates.map(String).includes(savedBaudrate)) {
        selectedBaudrate.value = savedBaudrate;
    }
};

const listSerialPorts = () => {
    socket.emit('list_serial_ports');
};

const autoConnectReceiver = () => {
    socket.emit('auto_connect_receiver');
};

const connectReceiver = () => {
    if (!selectedSerialPort.value || !selectedBaudrate.value) {
        alert('Please select Serial Port and Baudrate.');
        return;
    }

    socket.emit('connect_receiver', {
        data: {
            serial_ports: selectedSerialPort.value,
            baudrate: selectedBaudrate.value
        }
    });
};

const disconnectRx = () => {
    socket.emit('disconnect_rx');
};

const clearLog = () => {
    logs.value = [];
};

const monVer = () => {
    socket.emit('mon_ver');
};

const enableNavPvt = () => {
    socket.emit('enable_nav_pvt');
};

const enableUsefulMsgs = () => {
    socket.emit('enable_useful_msgs');
};

const toggleRxOutput = () => {
    if (!rxConnected.value) {
        alert('No receiver connected.');
        return;
    }

    isLogging.value = !isLogging.value;
    localStorage.setItem('is_logging', String(isLogging.value));
    socket.emit(isLogging.value ? 'show_rx_output' : 'hide_rx_output');
};

const fetchRxStatus = () => {
    socket.emit('is_rx_connected');
};

const bindSocketEvents = () => {
    socket.on('available_serial_ports', (data) => {
        serialPorts.value = Array.isArray(data) ? data : [];
        appendLog(`Available serial ports: ${serialPorts.value.join(', ') || 'none'}`);
        tryLoadLatestConnection();
    });

    socket.on('connection_log', (data) => {
        appendLog(`${data.serial_port}, ${data.baudrate}, ${data.attempt}`);
    });

    socket.on('rx_connection_status', (data) => {
        rxConnected.value = Boolean(data.rx_connected);
        isLogging.value = Boolean(data.is_logging);
        localStorage.setItem('is_logging', String(isLogging.value));

        if (rxConnected.value) {
            lastSuccessfulConnection.value = data.stream || '';
            if (lastSuccessfulConnection.value) {
                localStorage.setItem('connection_details', lastSuccessfulConnection.value);
            }
            monVer();
        }
    });

    socket.on('mon-ver', (data) => {
        const payload = Array.isArray(data.data) ? data.data : [];
        monVerData.softwareVersion = payload[0] || '';
        monVerData.hardwareVersion = payload[1] || '';
        monVerData.extensions = payload.slice(2);
    });

    socket.on('log_rx_output', (data) => {
        appendLog(data.data);
    });

    socket.on('nav-pvt', (data) => {
        const payload = data.data || {};
        Object.assign(navPvt, payload);
        setMarkerPosition(payload.lat, payload.lon);
    });

    socket.on('message_response', (data) => {
        appendLog(data.data);
    });

    socket.on('test', (data) => {
        appendLog(`Test: ${JSON.stringify(data)}`);
    });
};

onMounted(() => {
    socket = createSocketClient();
    bindSocketEvents();
    initMap();

    listSerialPorts();
    fetchRxStatus();
    tryLoadLatestConnection();
});

onBeforeUnmount(() => {
    destroyMap();
    if (socket) {
        socket.disconnect();
    }
});
</script>

<template>
  <div class="main-container vue-shell">
    <ControlPanel
      :baudrates="baudrates"
      :serial-ports="serialPorts"
      :selected-serial-port="selectedSerialPort"
      :selected-baudrate="selectedBaudrate"
      :rx-connected="rxConnected"
      :is-logging="isLogging"
      :connection-details="lastSuccessfulConnection"
    @serial-port-change="selectedSerialPort = $event"
    @baudrate-change="selectedBaudrate = $event"
      @list-ports="listSerialPorts"
      @auto-connect="autoConnectReceiver"
      @connect-receiver="connectReceiver"
      @disconnect-receiver="disconnectRx"
      @poll-mon-ver="monVer"
      @enable-nav-pvt="enableNavPvt"
      @toggle-rx-output="toggleRxOutput"
      @enable-useful-msgs="enableUsefulMsgs"
      @clear-log="clearLog"
    />

    <TelemetryPanel :mon-ver-data="monVerData" :nav-pvt="navPvt" :nav-pvt-fields="NAV_PVT_FIELDS" />

    <section class="panel map-wrapper">
      <div ref="mapElement" class="map-canvas"></div>
    </section>

    <LogPanel :logs="logs" :is-logging="isLogging" />
  </div>
</template>
