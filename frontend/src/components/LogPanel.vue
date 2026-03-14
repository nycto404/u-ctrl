<script setup>
defineProps({
    logs: {
        type: Array,
        required: true
    },
    isLogging: {
        type: Boolean,
        required: true
    }
});
</script>

<template>
  <section class="panel log-container">
    <div class="log-header">
      <h4>Logs</h4>
      <span class="status-chip" :class="isLogging ? 'status-on' : 'status-off'">
        {{ isLogging ? 'Streaming' : 'Idle' }}
      </span>
    </div>
    <div class="logs" id="logs">
      <p v-for="(entry, index) in logs" :key="`${index}-${entry}`">{{ entry }}</p>
    </div>
  </section>
</template>
