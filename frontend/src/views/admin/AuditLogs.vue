<template>
  <div>
    <div class="page-header"><h1>Audit Logs</h1><p>Track all changes made to goals, sheets, and system entities</p></div>
    <div class="card">
      <div style="display:flex;gap:8px;margin-bottom:16px">
        <select v-model="filterEntity" class="form-select" style="max-width:180px" @change="load">
          <option value="">All Entities</option>
          <option value="goal">Goal</option>
          <option value="goal_sheet">Goal Sheet</option>
          <option value="checkin">Check-in</option>
          <option value="achievement">Achievement</option>
          <option value="cycle">Cycle</option>
        </select>
        <select v-model="filterAction" class="form-select" style="max-width:180px" @change="load">
          <option value="">All Actions</option>
          <option value="created">Created</option>
          <option value="updated">Updated</option>
          <option value="submitted">Submitted</option>
          <option value="approved">Approved</option>
          <option value="returned">Returned</option>
          <option value="unlock_requested">Unlock Requested</option>
          <option value="unlock_accepted">Unlock Accepted</option>
          <option value="unlock_rejected">Unlock Rejected</option>
          <option value="deleted">Deleted</option>
        </select>
      </div>
      <div class="table-responsive"><table class="data-table">
        <thead><tr><th>Timestamp</th><th>User</th><th>Entity</th><th>Action</th><th>Description</th><th>Changes</th></tr></thead>
        <tbody>
          <tr v-for="l in logs" :key="l.id">
            <td style="font-size:0.8rem;white-space:nowrap">{{ formatDate(l.timestamp) }}</td>
            <td><strong style="font-size:0.85rem">{{ l.changed_by_name }}</strong></td>
            <td><span class="badge badge-default">{{ l.entity_type }} #{{ l.entity_id }}</span></td>
            <td><span class="badge" :class="actionBadge(l.action)">{{ l.action }}</span></td>
            <td style="font-size:0.8rem;color:var(--text-secondary);max-width:250px">{{ l.description || '—' }}</td>
            <td>
              <button v-if="l.old_values || l.new_values" class="btn btn-ghost btn-sm" @click="viewDiff = l">👁️ View</button>
            </td>
          </tr>
        </tbody>
      </table></div>
      <div style="display:flex;justify-content:center;gap:8px;margin-top:16px">
        <button class="btn btn-sm btn-secondary" :disabled="page <= 1" @click="page--;load()">← Prev</button>
        <span style="font-size:0.85rem;padding:6px 12px">Page {{ page }} of {{ totalPages }}</span>
        <button class="btn btn-sm btn-secondary" :disabled="page >= totalPages" @click="page++;load()">Next →</button>
      </div>
    </div>

    <div v-if="viewDiff" class="modal-overlay" @click.self="viewDiff = null">
      <div class="modal">
        <div class="modal-header"><h3>Change Details</h3><button class="btn btn-ghost btn-sm" @click="viewDiff = null">✕</button></div>
        <div class="modal-body">
          <div v-if="viewDiff.old_values"><h4 style="color:var(--danger);font-size:0.85rem;margin-bottom:8px">Old Values</h4><pre style="background:var(--bg-tertiary);padding:12px;border-radius:8px;font-size:0.75rem;overflow:auto">{{ JSON.stringify(viewDiff.old_values, null, 2) }}</pre></div>
          <div v-if="viewDiff.new_values" style="margin-top:16px"><h4 style="color:var(--success);font-size:0.85rem;margin-bottom:8px">New Values</h4><pre style="background:var(--bg-tertiary);padding:12px;border-radius:8px;font-size:0.75rem;overflow:auto">{{ JSON.stringify(viewDiff.new_values, null, 2) }}</pre></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../services/api'

const logs = ref([])
const page = ref(1)
const totalPages = ref(1)
const filterEntity = ref('')
const filterAction = ref('')
const viewDiff = ref(null)

onMounted(load)

async function load() {
  const params = { page: page.value, per_page: 15 }
  if (filterEntity.value) params.entity_type = filterEntity.value
  if (filterAction.value) params.action = filterAction.value
  const { data } = await api.get('/admin/audit-logs', { params })
  logs.value = data.logs
  totalPages.value = data.pages
}

function formatDate(d) { return d ? new Date(d).toLocaleString() : '—' }

function actionBadge(a) {
  const map = { created: 'badge-success', updated: 'badge-info', submitted: 'badge-warning',
    approved: 'badge-success', returned: 'badge-danger', unlocked: 'badge-accent', deleted: 'badge-danger' }
  return map[a] || 'badge-default'
}
</script>

