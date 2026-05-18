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
        <div style="display:flex;gap:8px">
          <button v-if="!c.is_active" class="btn btn-sm btn-secondary" @click="activateCycle(c.id)">Set Active</button>
          <button class="btn btn-sm btn-secondary" @click="startEditWindows(c)">✏️ Edit Windows</button>
          <button v-if="!c.is_active" class="btn btn-sm btn-ghost" style="color:var(--danger)" @click="deleteCycle(c)">🗑 Delete</button>
        </div>
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

    <!-- Create Cycle Modal -->
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

    <!-- Edit Windows Modal -->
    <div v-if="showEditModal" class="modal-overlay" @click.self="showEditModal = false">
      <div class="modal" style="max-width:600px">
        <div class="modal-header"><h3>Edit Cycle Windows — {{ editCycleName }}</h3><button class="btn btn-ghost btn-sm" @click="showEditModal = false">✕</button></div>
        <div class="modal-body">
          <div v-for="w in editWindows" :key="w.id" style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;align-items:end;margin-bottom:12px;padding-bottom:12px;border-bottom:1px solid var(--border-light)">
            <div class="form-group" style="margin:0">
              <label class="form-label">{{ w.phase_label }}</label>
            </div>
            <div class="form-group" style="margin:0">
              <label class="form-label">Opens</label>
              <input v-model="w.opens_at" type="date" class="form-input" />
            </div>
            <div class="form-group" style="margin:0">
              <label class="form-label">Closes</label>
              <input v-model="w.closes_at" type="date" class="form-input" />
            </div>
          </div>
        </div>
        <div class="modal-footer"><button class="btn btn-secondary" @click="showEditModal = false">Cancel</button><button class="btn btn-primary" @click="saveWindows">💾 Save Changes</button></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, inject } from 'vue'
import api from '../../services/api'

const toast = inject('toast')
const cycles = ref([])
const showCreateModal = ref(false)
const showEditModal = ref(false)
const newCycle = ref({ name: '', year: 2027, is_active: false })
const editCycleId = ref(null)
const editCycleName = ref('')
const editWindows = ref([])

onMounted(loadCycles)

async function loadCycles() {
  const { data } = await api.get('/admin/cycles')
  cycles.value = data.cycles
}

async function createCycle() {
  try {
    await api.post('/admin/cycles', newCycle.value)
    showCreateModal.value = false
    loadCycles()
    toast?.success('Cycle created!')
  } catch(e) { toast?.error(e.response?.data?.error || 'Failed to create cycle') }
}

async function activateCycle(id) {
  await api.put(`/admin/cycles/${id}`, { is_active: true })
  loadCycles()
  toast?.success('Cycle activated!')
}

async function deleteCycle(c) {
  if (!confirm(`Are you sure you want to delete "${c.name}"? This cannot be undone.`)) return
  try {
    await api.delete(`/admin/cycles/${c.id}`)
    loadCycles()
    toast?.success('Cycle deleted!')
  } catch(e) { toast?.error(e.response?.data?.error || 'Failed to delete cycle') }
}

function startEditWindows(c) {
  editCycleId.value = c.id
  editCycleName.value = c.name
  editWindows.value = c.windows.map(w => ({ ...w }))
  showEditModal.value = true
}

async function saveWindows() {
  try {
    await api.put(`/admin/cycles/${editCycleId.value}/windows`, { windows: editWindows.value })
    showEditModal.value = false
    loadCycles()
    toast?.success('Cycle windows updated!')
  } catch(e) { toast?.error(e.response?.data?.error || 'Failed to update windows') }
}
</script>
