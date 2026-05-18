<template>
  <div>
    <div class="page-header" style="display:flex;justify-content:space-between;align-items:center">
      <div><h1>Escalation Management</h1><p>Configure rules and monitor escalation logs</p></div>
      <button class="btn btn-primary" @click="showCreate = true">➕ Add Rule</button>
    </div>

    <div class="card" style="margin-bottom:20px">
      <div class="card-header"><h3 class="card-title">⚙️ Escalation Rules</h3></div>
      <div class="table-responsive" v-if="rules.length"><table class="data-table">
        <thead><tr><th>Trigger Event</th><th>Threshold (days)</th><th>Interval (days)</th><th>Notify Employee</th><th>Notify Manager</th><th>Notify HR</th><th>Status</th></tr></thead>
        <tbody>
          <tr v-for="r in rules" :key="r.id">
            <td><span class="badge badge-warning">{{ formatEvent(r.trigger_event) }}</span></td>
            <td><strong>{{ r.days_threshold }}</strong> days</td>
            <td>{{ r.escalation_interval }} days</td>
            <td><span :class="r.notify_employee?'text-success':'text-muted'">{{ r.notify_employee ? '✅' : '—' }}</span></td>
            <td><span :class="r.notify_manager?'text-success':'text-muted'">{{ r.notify_manager ? '✅' : '—' }}</span></td>
            <td><span :class="r.notify_hr?'text-success':'text-muted'">{{ r.notify_hr ? '✅' : '—' }}</span></td>
            <td><span class="badge badge-dot" :class="r.is_active?'badge-success':'badge-danger'">{{ r.is_active ? 'Active' : 'Inactive' }}</span></td>
          </tr>
        </tbody>
      </table></div>
      <div v-else class="empty-state" style="padding:24px"><div class="empty-state-icon">⚙️</div><h3>No rules configured</h3></div>
    </div>

    <div class="card">
      <div class="card-header"><h3 class="card-title">📋 Escalation Logs</h3></div>
      <div class="table-responsive" v-if="logs.length"><table class="data-table">
        <thead><tr><th>Triggered</th><th>Event</th><th>User</th><th>Level</th><th>Message</th><th>Status</th></tr></thead>
        <tbody>
          <tr v-for="l in logs" :key="l.id">
            <td style="font-size:0.8rem;white-space:nowrap">{{ formatDate(l.triggered_at) }}</td>
            <td><span class="badge badge-warning">{{ formatEvent(l.trigger_event) }}</span></td>
            <td><strong style="font-size:0.85rem">{{ l.target_user_name }}</strong></td>
            <td><span class="badge badge-info">L{{ l.level }}</span></td>
            <td style="font-size:0.82rem;color:var(--text-secondary);max-width:250px">{{ l.message || '—' }}</td>
            <td><span class="badge badge-dot" :class="l.resolved?'badge-success':'badge-danger'">{{ l.resolved ? 'Resolved' : 'Open' }}</span></td>
          </tr>
        </tbody>
      </table></div>
      <div v-else class="empty-state" style="padding:24px"><div class="empty-state-icon">📋</div><h3>No escalation logs</h3><p>Escalations will appear here when triggered</p></div>
    </div>

    <!-- Create Rule Modal -->
    <div v-if="showCreate" class="modal-overlay" @click.self="showCreate=false">
      <div class="modal">
        <div class="modal-header"><h3>Create Escalation Rule</h3><button class="btn btn-ghost btn-sm" @click="showCreate=false">✕</button></div>
        <div class="modal-body">
          <div class="form-group"><label class="form-label">Trigger Event</label>
            <select v-model="form.trigger_event" class="form-select">
              <option value="goal_not_submitted">Goal Not Submitted</option>
              <option value="goal_not_approved">Goal Not Approved</option>
              <option value="checkin_overdue">Check-in Overdue</option>
            </select>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
            <div class="form-group"><label class="form-label">Days Threshold</label><input v-model.number="form.days_threshold" type="number" class="form-input" min="1" /></div>
            <div class="form-group"><label class="form-label">Escalation Interval</label><input v-model.number="form.escalation_interval" type="number" class="form-input" min="1" /></div>
          </div>
          <div style="display:flex;gap:16px;margin-top:8px">
            <label style="display:flex;align-items:center;gap:6px;font-size:0.85rem"><input type="checkbox" v-model="form.notify_employee" /> Employee</label>
            <label style="display:flex;align-items:center;gap:6px;font-size:0.85rem"><input type="checkbox" v-model="form.notify_manager" /> Manager</label>
            <label style="display:flex;align-items:center;gap:6px;font-size:0.85rem"><input type="checkbox" v-model="form.notify_hr" /> HR</label>
          </div>
        </div>
        <div class="modal-footer"><button class="btn btn-secondary" @click="showCreate=false">Cancel</button><button class="btn btn-primary" @click="createRule">Create</button></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, inject } from 'vue'
import api from '../../services/api'

const toast = inject('toast')
const rules = ref([])
const logs = ref([])
const showCreate = ref(false)
const form = ref({ trigger_event:'goal_not_submitted', days_threshold:7, escalation_interval:3, notify_employee:true, notify_manager:true, notify_hr:false })

onMounted(async () => {
  const [r, l] = await Promise.all([api.get('/admin/escalation-rules'), api.get('/admin/escalation-logs')])
  rules.value = r.data.rules
  logs.value = l.data.logs
})

function formatEvent(e) { return { goal_not_submitted:'Goal Not Submitted', goal_not_approved:'Goal Not Approved', checkin_overdue:'Check-in Overdue' }[e] || e }
function formatDate(d) { return d ? new Date(d).toLocaleString() : '—' }

async function createRule() {
  try {
    await api.post('/admin/escalation-rules', form.value)
    showCreate.value = false
    const { data } = await api.get('/admin/escalation-rules')
    rules.value = data.rules
    toast?.success('Escalation rule created!')
  } catch(e) { toast?.error(e.response?.data?.error || 'Failed') }
}
</script>

<style scoped>
.text-success { color: var(--success); }
.text-muted { color: var(--text-muted); }
</style>

