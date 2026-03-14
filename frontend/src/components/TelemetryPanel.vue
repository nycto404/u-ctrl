<script setup>
defineProps({
    monVerData: {
        type: Object,
        required: true
    },
    navPvt: {
        type: Object,
        required: true
    },
    navPvtFields: {
        type: Array,
        required: true
    }
});
</script>

<template>
  <section class="panel receiver-data">
    <div class="receiver-info">
      <h4>MON-VER</h4>
      <table class="mon-ver-table">
        <tr>
          <th>Software Version</th>
          <td>{{ monVerData.softwareVersion || '-' }}</td>
        </tr>
        <tr>
          <th>Hardware Version</th>
          <td>{{ monVerData.hardwareVersion || '-' }}</td>
        </tr>
        <tr>
          <th>Extensions</th>
          <td>
            <span v-if="!monVerData.extensions.length">-</span>
            <ul v-else class="extensions-list">
              <li v-for="extension in monVerData.extensions" :key="extension">{{ extension }}</li>
            </ul>
          </td>
        </tr>
      </table>
    </div>

    <div class="nav-pvt-data">
      <h4>NAV-PVT Data</h4>
      <table class="nav-pvt-data-table">
        <tr v-for="field in navPvtFields" :key="field.key">
          <th>{{ field.label }}</th>
          <td>{{ navPvt[field.key] ?? '-' }}</td>
        </tr>
      </table>
    </div>
  </section>
</template>
