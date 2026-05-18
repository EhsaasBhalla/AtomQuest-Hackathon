<template>
  <div>
    <div class="page-header" style="display:flex;justify-content:space-between;align-items:center">
      <div>
        <h1>Review: {{ employee?.full_name }}</h1>
        <p>{{ employee?.designation }} • {{ employee?.department_name }}</p>
      </div>
      <div style="display:flex;gap:8px" v-if="sheet?.status === 'submitted'">
        <button class="btn btn-success" @click="approveSheet">✅ Approve</button>
        <button class="btn btn-danger" @click="showReturnModal = true">🔄 Return</button>
      </div>
      <div v-else-if="sheet" style="display:flex;gap:8px;align-items:center">
        <span class="badge" :class="sheet.status==='approved'?'badge-success':'badge-default'" style="font-size:0.9rem;padding:8px 16px">
          {{ sheet.status?.toUpperCase() }}
        </span>
        <button v-if="sheet.status === 'approved' && isAdmin" class="btn btn-sm btn-secondary" @click="unlockSheet" title="Admin: Unlock for editing">
          🔓 Unlock Sheet
        </button>
      </div>
    </div>

    <div v-if="loading" class="card"><div class="skeleton skeleton-card"></div></div>

    <div v-else-if="sheet">
      <div class="card" style="margin-bottom:20px">
        <div style="display:flex;justify-content:space-between;align-items:center">
          <div style="display:flex;gap:12px;align-items:center">
            <span class="badge" :class="sheet.status==='approved'?'badge-success':'badge-warning'">{{ sheet.status }}</span>
            <span style="font-size:0.85rem;color:var(--text-muted)">Total Weightage: <strong>{{ computedTotal }}%</strong> • {{ sheet.goal_count }} goals</span>
          </div>
          <span v-if="hasEdits" class="badge badge-info">Unsaved edits</span>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Goals {{ sheet.status === 'submitted' ? '(Click values to edit)' : '' }}</h3>
        </div>
        <div class="table-responsive"><table class="data-table">
          <thead><tr><th>#</th><th>Goal</th><th>Thrust Area</th><th>UoM</th><th>Target</th><th>Weightage</th></tr></thead>
          <tbody>
            <tr v-for="(g, i) in editableGoals" :key="g.id">
              <td>{{ i + 1 }}</td>
              <td>
                <strong>{{ g.title }}</strong>
                <p style="font-size:0.75rem;color:var(--text-muted);margin-top:2px">{{ g.description }}</p>
              </td>
              <td><span class="badge badge-default">{{ g.thrust_area }}</span></td>
              <td>{{ g.uom_type }}</td>
              <td>
                <template v-if="sheet.status === 'submitted' && !g.is_target_locked">
                  <input v-if="g.uom_type !== 'timeline'" v-model.number="g.edit_target" type="number" class="inline-input" @change="g.dirty = true" />
                  <input v-else v-model="g.edit_target_date" type="date" class="inline-input" @change="g.dirty = true" />
                </template>
                <template v-else>{{ g.target_value || g.target_date || '0' }}</template>
              </td>
              <td>
                <template v-if="sheet.status === 'submitted'">
                  <div style="display:flex;align-items:center;gap:6px">
                    <input v-model.number="g.edit_weightage" type="number" class="inline-input" style="width:60px" min="10" @change="g.dirty = true" />
                    <span style="font-size:0.8rem">%</span>
                    <button v-if="g.dirty" class="btn btn-sm btn-primary" @click="saveGoalEdit(g)" style="padding:3px 8px">💾</button>
                  </div>
                </template>
                <template v-else><strong>{{ g.weightage }}%</strong></template>
              </td>
            </tr>
          </tbody>
        </table></div>
        <div v-if="sheet.status === 'submitted'" style="margin-top:12px;padding-top:12px;border-top:1px solid var(--border-light);display:flex;justify-content:space-between">
          <span style="font-size:0.82rem;color:var(--text-muted)">Total: <strong :style="{color:computedTotal===100?'var(--success)':'var(--danger)'}">{{ computedTotal }}%</strong></span>
          <span v-if="computedTotal !== 100" style="font-size:0.82rem;color:var(--danger)">⚠️ Must equal 100%</span>
        </div>
      </div>
    </div>

    <!-- Return Modal -->
    <div v-if="showReturnModal" class="modal-overlay" @click.self="showReturnModal = false">
      <div class="modal">
        <div class="modal-header"><h3>Return Goal Sheet</h3><button class="btn btn-ghost btn-sm" @click="showReturnModal = false">✕</button></div>
        <div class="modal-body">
          <div class="form-group"><label class="form-label">Reason / Comments</label><textarea v-model="returnComment" class="form-textarea" rows="4" placeholder="Explain what needs to be changed..."></textarea></div>
        </div>
        <div class="modal-footer"><button class="btn btn-secondary" @click="showReturnModal = false">Cancel</button><button class="btn btn-danger" @click="returnSheet">Return Sheet</button></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, inject } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import api from '../../services/api'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const toast = inject('toast')
const isAdmin = computed(() => auth.userRole === 'admin')
const employee = ref(null)
const sheet = ref(null)
const editableGoals = ref([])
const showReturnModal = ref(false)
const returnComment = ref('')
const loading = ref(true)

onMounted(async () => {
  try {
    const { data } = await api.get(`/manager/team/${route.params.employeeId}/sheet`)
    employee.value = data.employee
    sheet.value = data.sheet
    editableGoals.value = data.sheet.goals.map(g => ({
      ...g, edit_target: g.target_value, edit_target_date: g.target_date, edit_weightage: g.weightage, dirty: false
    }))
  } finally { loading.value = false }
})

const computedTotal = computed(() => editableGoals.value.reduce((s, g) => s + (g.edit_weightage || g.weightage), 0))
const hasEdits = computed(() => editableGoals.value.some(g => g.dirty))

async function saveGoalEdit(g) {
  try {
    const payload = { target_value: g.edit_target, target_date: g.edit_target_date, weightage: g.edit_weightage }
    await api.put(`/manager/team/${route.params.employeeId}/goals/${g.id}`, payload)
    g.target_value = g.edit_target; g.target_date = g.edit_target_date; g.weightage = g.edit_weightage; g.dirty = false
    toast?.success('Goal updated')
  } catch(e) { toast?.error(e.response?.data?.error || 'Failed to update') }
}

async function approveSheet() {
  if (computedTotal.value !== 100) { toast?.error('Total weightage must be 100%'); return }
  if (!confirm('Approve this goal sheet? Goals will be locked.')) return
  try {
    await api.post(`/manager/team/${route.params.employeeId}/sheet/approve`, {})
    toast?.success('Goal sheet approved!', '✅ Approved')
    router.push('/team')
  } catch(e) { toast?.error(e.response?.data?.error || 'Failed') }
}

async function returnSheet() {
  try {
    await api.post(`/manager/team/${route.params.employeeId}/sheet/return`, { comment: returnComment.value })
    showReturnModal.value = false
    toast?.success('Goal sheet returned for rework')
    router.push('/team')
  } catch(e) { toast?.error(e.response?.data?.error || 'Failed') }
}

async function unlockSheet() {
  if (!confirm('Unlock this goal sheet? It will be returned for editing.')) return
  try {
    const goalId = editableGoals.value[0]?.id
    if (!goalId) return
    await api.post(`/admin/goals/${goalId}/unlock`)
    toast?.success('Goal sheet unlocked for editing', '🔓 Unlocked')
    location.reload()
  } catch(e) { toast?.error(e.response?.data?.error || 'Failed to unlock') }
}
</script>

<style scoped>
.inline-input {
  padding: 5px 8px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-family: inherit;
  font-size: 0.82rem;
  width: 90px;
  color: var(--text-primary);
  background: var(--bg-secondary);
  transition: var(--transition);
}
.inline-input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 2px rgba(79,70,229,0.15);
}
</style>

