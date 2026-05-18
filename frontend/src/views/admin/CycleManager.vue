<template>
  <div>
    <div class="page-header" style="display:flex;justify-content:space-between;align-items:center">
      <div><h1>Cycle Management</h1><p>Configure performance cycles and quarterly windows</p></div>
      <button class="btn btn-primary" @click="showCreateModal = true">➕ New Cycle</button>
    </div>

    <div v-for="c in cycles" :key="c.id" class="card" style="margin-bottom:16px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
        <div style="display:flex;align-items:center;gap:12px">
          <h3 style="font-size:1.1rem;font-weight:600">{{ c.name }}</h3>
          <span v-if="c.is_active" class="badge badge-success badge-dot">Active</span>
          <span v-else class="badge badge-default">Inactive</span>
        </div>
        <button v-if="!c.is_active" class="btn btn-sm btn-secondary" @click="activateCycle(c.id)">Set Active</button>
      </div>
      <div class="table-responsive"><table class="data-table">
        <thead><tr><th>Phase</th><th>Opens</th><th>Closes</th><th>Status</th></tr></thead>
        <tbody>
          <tr v-for="w in c.windows" :key="w.id">
            <td><strong>{{ w.phase_label }}</strong></td>
            <td>{{ w.opens_at }}</td>
            <td>{{ w.closes_at }}</td>
            <td>
              <span class="badge badge-dot" :class="w.status === 'active' ? 'badge-success' : w.status === 'upcoming' ? 'badge-info' : 'badge-default'">
                {{ w.status }}
              </span>
            </td>
          </tr>
        </tbody>
      </table></div>
    </div>

    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="modal">
        <div class="modal-header"><h3>Create New Cycle</h3><button class="btn btn-ghost btn-sm" @click="showCreateModal = false">✕</button></div>
        <div class="modal-body">
          <div class="form-group"><label class="form-label">Cycle Name</label><input v-model="newCycle.name" class="form-input" placeholder="e.g., FY 2027-28" /></div>
          <div class="form-group"><label class="form-label">Year</label><input v-model.number="newCycle.year" type="number" class="form-input" /></div>
          <label style="display:flex;align-items:center;gap:8px;font-size:0.85rem"><input type="checkbox" v-model="newCycle.is_active" /> Set as active cycle</label>
        </div>
        <div class="modal-footer"><button class="btn btn-secondary" @click="showCreateModal = false">Cancel</button><button class="btn btn-primary" @click="createCycle">Create</button></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../services/api'

const cycles = ref([])
const showCreateModal = ref(false)
const newCycle = ref({ name: '', year: 2027, is_active: false })

onMounted(loadCycles)

async function loadCycles() {
  const { data } = await api.get('/admin/cycles')
  cycles.value = data.cycles
}

async function createCycle() {
  await api.post('/admin/cycles', newCycle.value)
  showCreateModal.value = false
  loadCycles()
}

async function activateCycle(id) {
  await api.put(`/admin/cycles/${id}`, { is_active: true })
  loadCycles()
}
</script>

