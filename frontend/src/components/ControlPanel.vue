<script setup>
const props = defineProps({
    baudrates: {
        type: Array,
        required: true
    },
    serialPorts: {
        type: Array,
        required: true
    },
    selectedSerialPort: {
        type: String,
        required: true
    },
    selectedBaudrate: {
        type: String,
        required: true
    },
    rxConnected: {
        type: Boolean,
        required: true
    },
    isLogging: {
        type: Boolean,
        required: true
    },
    connectionDetails: {
        type: String,
        required: true
    }
});

const emit = defineEmits([
  'serialPortChange',
  'baudrateChange',
    'listPorts',
    'autoConnect',
    'connectReceiver',
    'disconnectReceiver',
    'pollMonVer',
    'enableNavPvt',
    'toggleRxOutput',
    'enableUsefulMsgs',
    'clearLog'
]);
</script>

<template>
  <section class="panel controls-panel">
    <div class="buttons">
      <button class="btn btn-primary" @click="emit('listPorts')">List Serial Ports</button>
      <button class="btn btn-primary" :disabled="props.rxConnected" @click="emit('autoConnect')">Autoconnect</button>
      <button class="btn btn-danger" :disabled="!props.rxConnected" @click="emit('disconnectReceiver')">Disconnect</button>
      <button class="btn btn-secondary" @click="emit('clearLog')">Clear Log</button>
      <button class="btn btn-primary" :disabled="!props.rxConnected" @click="emit('pollMonVer')">MON-VER</button>
      <button class="btn btn-primary" :disabled="!props.rxConnected" @click="emit('enableNavPvt')">Enable NAV-PVT</button>
      <button class="btn btn-primary" :disabled="!props.rxConnected" @click="emit('toggleRxOutput')">
        {{ props.isLogging ? 'Disable RX output' : 'Enable RX output' }}
      </button>
      <button class="btn btn-info" :disabled="!props.rxConnected" @click="emit('enableUsefulMsgs')">Enable useful messages</button>
    </div>

    <div class="manual-connect">
      <select
        class="form-select w-100"
        :value="props.selectedSerialPort"
        @change="emit('serialPortChange', $event.target.value)"
      >
        <option disabled value="">Serial Port</option>
        <option v-for="port in props.serialPorts" :key="port" :value="port">{{ port }}</option>
      </select>

      <select
        class="form-select w-100"
        :value="props.selectedBaudrate"
        @change="emit('baudrateChange', $event.target.value)"
      >
        <option disabled value="">Baudrate</option>
        <option v-for="rate in props.baudrates" :key="rate" :value="String(rate)">{{ rate }}</option>
      </select>

      <button class="btn btn-primary w-100" :disabled="props.rxConnected" @click="emit('connectReceiver')">Connect</button>
    </div>

    <div class="connection-meta">
      <div class="connection-status" :class="{ connected: props.rxConnected }" :title="props.connectionDetails || 'Disconnected'">
        <i class="fa-solid fa-link"></i>
      </div>
      <p class="connection-text">{{ props.rxConnected ? 'Connected' : 'Disconnected' }}</p>
    </div>
  </section>
</template>
