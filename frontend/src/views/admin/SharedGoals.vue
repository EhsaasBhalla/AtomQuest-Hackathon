<template>
  <div>
    <div class="page-header" style="display:flex;justify-content:space-between;align-items:center">
      <div><h1>Shared Goals</h1><p>Create and push departmental KPIs to employees</p></div>
      <button class="btn btn-primary" @click="showCreate = true">➕ Create Shared Goal</button>
    </div>

    <div v-if="loading" class="card"><div class="skeleton skeleton-card"></div></div>

    <div v-else-if="goals.length">
      <div v-for="sg in goals" :key="sg.id" class="card" style="margin-bottom:16px">
        <div style="display:flex;justify-content:space-between;align-items:start">
          <div>
            <h3 style="font-size:1rem;font-weight:600">{{ sg.title }}</h3>
            <p style="font-size:0.8rem;color:var(--text-muted);margin-top:4px">{{ sg.description }}</p>
            <div style="display:flex;gap:8px;margin-top:8px">
              <span class="badge badge-default">{{ sg.thrust_area }}</span>
              <span class="badge badge-info">{{ sg.uom_type }}</span>
              <span class="badge badge-accent">Target: {{ sg.target_value || sg.target_date || '0' }}</span>
              <span class="badge badge-success">{{ sg.recipient_count }} recipients</span>
            </div>
          </div>
          <button class="btn btn-sm btn-primary" @click="openPush(sg)">📤 Push to Employees</button>
        </div>
      </div>
    </div>

    <div v-else class="card empty-state">
      <div class="empty-state-icon">🎯</div><h3>No shared goals yet</h3><p>Create a shared goal to push KPIs across your team</p>
    </div>

    <!-- Create Modal -->
    <div v-if="showCreate" class="modal-overlay" @click.self="showCreate = false">
      <div class="modal">
        <div class="modal-header"><h3>Create Shared Goal</h3><button class="btn btn-ghost btn-sm" @click="showCreate = false">✕</button></div>
        <div class="modal-body">
          <div class="form-group"><label class="form-label">Title *</label><input v-model="form.title" class="form-input" required /></div>
          <div class="form-group"><label class="form-label">Description</label><textarea v-model="form.description" class="form-textarea" rows="2"></textarea></div>
          <div class="form-group"><label class="form-label">Thrust Area *</label>
            <select v-model="form.thrust_area" class="form-select"><option v-for="t in areas" :key="t" :value="t">{{ t }}</option></select>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
            <div class="form-group"><label class="form-label">UoM *</label>
              <select v-model="form.uom_type" class="form-select"><option value="numeric_min">Numeric (Higher)</option><option value="numeric_max">Numeric (Lower)</option><option value="percent_min">% (Higher)</option><option value="percent_max">% (Lower)</option><option value="timeline">Timeline</option><option value="zero">Zero-based</option></select>
            </div>
            <div class="form-group"><label class="form-label">Target</label><input v-model.number="form.target_value" type="number" class="form-input" /></div>
          </div>
        </div>
        <div class="modal-footer"><button class="btn btn-secondary" @click="showCreate = false">Cancel</button><button class="btn btn-primary" @click="createGoal">Create</button></div>
      </div>
    </div>

    <!-- Push Modal -->
    <div v-if="showPush" class="modal-overlay" @click.self="showPush = false">
      <div class="modal">
        <div class="modal-header"><h3>Push: {{ pushTarget?.title }}</h3><button class="btn btn-ghost btn-sm" @click="showPush = false">✕</button></div>
        <div class="modal-body" style="max-height: 60vh; overflow-y: auto;">
          <p style="font-size:0.85rem;margin-bottom:12px;color:var(--text-secondary)">Select employees to receive this shared goal:</p>
          <div v-for="(mgrs, deptName) in groupedEmployees" :key="deptName" style="margin-bottom: 20px;">
            <div style="font-size:0.85rem; font-weight:700; color:var(--text-primary); margin-bottom:8px; border-bottom:2px solid var(--border-light); padding-bottom:6px;">{{ deptName }}</div>
            <div v-for="(emps, mgrName) in mgrs" :key="mgrName" style="margin-left: 8px; margin-bottom: 12px;">
              <div style="font-size:0.75rem; font-weight:600; color:var(--text-muted); margin-bottom:6px; text-transform:uppercase; letter-spacing:0.05em;">Reporting to: {{ mgrName }}</div>
              <div v-for="u in emps" :key="u.id" class="push-item" style="margin-left: 8px;">
                <label style="display:flex;align-items:center;gap:10px;cursor:pointer" :style="{ opacity: pushTarget?.pushed_to?.includes(u.id) ? '0.6' : '1' }">
                  <input type="checkbox" v-model="selectedEmps" :value="u.id" :disabled="pushTarget?.pushed_to?.includes(u.id)" />
                  <div class="avatar" style="width:28px;height:28px;font-size:0.65rem" :style="{background:u.avatar_color}">{{ u.full_name?.charAt(0) }}</div>
                  <div style="flex: 1">
                    <div style="display:flex; align-items:center; gap:8px">
                      <strong style="font-size:0.82rem">{{ u.full_name }}</strong>
                      <span v-if="pushTarget?.pushed_to?.includes(u.id)" class="badge badge-success" style="font-size: 0.6rem; padding: 2px 6px">Already Pushed</span>
                    </div>
                    <div style="font-size:0.72rem;color:var(--text-muted);text-transform:capitalize;">{{ u.role }} &bull; {{ u.email }}</div>
                  </div>
                </label>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer"><button class="btn btn-secondary" @click="showPush = false">Cancel</button><button class="btn btn-primary" @click="pushGoal" :disabled="selectedEmps.length === (pushTarget?.pushed_to?.length || 0)">Push to New Employees</button></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, inject, computed } from 'vue'
import api from '../../services/api'

const toast = inject('toast')
const goals = ref([])
const employees = ref([])
const loading = ref(true)
const showCreate = ref(false)
const showPush = ref(false)
const pushTarget = ref(null)
const selectedEmps = ref([])
const areas = ['Revenue Growth','Customer Satisfaction','Product Quality','Innovation','Operational Excellence','People Development']
const form = ref({ title:'', description:'', thrust_area:'Revenue Growth', uom_type:'numeric_min', target_value:null })

const groupedEmployees = computed(() => {
  const groups = {}
  employees.value.forEach(emp => {
    const dept = emp.department_name || 'Unassigned Department'
    const mgr = emp.manager_name || 'No Manager'
    if (!groups[dept]) groups[dept] = {}
    if (!groups[dept][mgr]) groups[dept][mgr] = []
    groups[dept][mgr].push(emp)
  })
  return groups
})

onMounted(async () => {
  try {
    const [sg, us] = await Promise.all([api.get('/shared-goals/'), api.get('/manager/team')])
    goals.value = sg.data.shared_goals
    employees.value = us.data.team
  } finally { loading.value = false }
})

async function createGoal() {
  try {
    await api.post('/shared-goals/', form.value)
    showCreate.value = false
    const { data } = await api.get('/shared-goals/')
    goals.value = data.shared_goals
    toast?.success('Shared goal created!')
  } catch(e) { toast?.error(e.response?.data?.error || 'Failed') }
}

function openPush(sg) { 
  pushTarget.value = sg; 
  // Automatically select employees who already received it so checkboxes show as checked
  selectedEmps.value = [...(sg.pushed_to || [])]; 
  showPush.value = true; 
}

async function pushGoal() {
  try {
    const newPushes = selectedEmps.value.filter(id => !(pushTarget.value.pushed_to || []).includes(id))
    await api.post(`/shared-goals/${pushTarget.value.id}/push`, { employee_ids: newPushes })
    showPush.value = false
    const { data } = await api.get('/shared-goals/')
    goals.value = data.shared_goals
    toast?.success(`Pushed to ${newPushes.length} new employees!`)
  } catch(e) { toast?.error(e.response?.data?.error || 'Failed') }
}
</script>

<style scoped>
.push-item { padding:8px 0; border-bottom:1px solid var(--border-light); }
.push-item:last-child { border:none; }
</style>
