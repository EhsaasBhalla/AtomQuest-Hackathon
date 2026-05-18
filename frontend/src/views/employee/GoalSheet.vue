<template>
  <div>
    <div class="page-header" style="display:flex;justify-content:space-between;align-items:center">
      <div>
        <h1>My Goal Sheet</h1>
        <p>FY 2026-27 • {{ statusLabel }}</p>
      </div>
      <div style="display:flex;gap:8px">
        <router-link v-if="canEdit" to="/goals/new" class="btn btn-primary">➕ Add Goal</router-link>
        <button v-if="canSubmit" class="btn btn-success" @click="submitSheet">🚀 Submit for Approval</button>
        <button v-if="gs.sheetStatus === 'approved' && isGoalSettingOpen && !gs.currentSheet.unlock_requested" class="btn btn-secondary" @click="showUnlockModal = true">🔓 Request Changes</button>
      </div>
    </div>

    <!-- Unlock Request Feedback -->
    <div v-if="gs.currentSheet?.unlock_requested" class="card" style="margin-bottom:20px;border-left:3px solid var(--info)">
      <strong style="color:var(--info)">🔓 Unlock Requested</strong>
      <p style="margin-top:6px;color:var(--text-secondary)">You have requested to change your goals. Waiting for manager approval.</p>
    </div>
    <div v-if="gs.currentSheet?.unlock_feedback && !gs.currentSheet?.unlock_requested" class="card" style="margin-bottom:20px;border-left:3px solid var(--accent)">
      <strong style="color:var(--accent)">💬 Manager Feedback (Goal Unlock)</strong>
      <p style="margin-top:6px;color:var(--text-secondary)">{{ gs.currentSheet.unlock_feedback }}</p>
    </div>

    <div class="card" style="margin-bottom:20px">
      <div style="display:flex;justify-content:space-between;margin-bottom:8px">
        <span class="form-label" style="margin:0">Total Weightage</span>
        <span class="form-label" style="margin:0" :style="{color: gs.totalWeightage===100?'var(--success)':'var(--danger)'}">
          {{ gs.totalWeightage }}% / 100%
        </span>
      </div>
      <div class="progress-bar" style="height:10px">
        <div class="progress-fill" :class="gs.totalWeightage===100?'success':gs.totalWeightage>100?'danger':'warning'"
          :style="{ width: Math.min(gs.totalWeightage, 100) + '%' }"></div>
      </div>
      <div style="display:flex;justify-content:space-between;margin-top:8px">
        <span style="font-size:0.75rem;color:var(--text-muted)">{{ gs.goalCount }} / 8 goals</span>
        <span v-if="gs.totalWeightage !== 100" style="font-size:0.75rem;color:var(--warning)">⚠️ Must equal 100% to submit</span>
        <span v-else style="font-size:0.75rem;color:var(--success)">✅ Ready to submit</span>
      </div>
    </div>

    <div v-if="gs.currentSheet?.return_comment && gs.sheetStatus === 'returned'" class="card" style="margin-bottom:20px;border-left:3px solid var(--danger)">
      <strong style="color:var(--danger)">🔄 Returned by Manager</strong>
      <p style="margin-top:6px;color:var(--text-secondary)">{{ gs.currentSheet.return_comment }}</p>
    </div>

    <div v-if="gs.loading" class="card">
      <div class="skeleton skeleton-heading"></div>
      <div v-for="i in 3" :key="i" class="skeleton skeleton-text" :style="{width: (90-i*10)+'%'}"></div>
    </div>

    <div class="card" v-else-if="gs.goals.length">
      <div class="card-header">
        <h3 class="card-title">Goals ({{ gs.goalCount }})</h3>
        <button class="btn btn-ghost btn-sm" @click="toggleSort">↕ Sort by {{ sortBy === 'weightage' ? 'Order' : 'Weightage' }}</button>
      </div>
      <div class="table-responsive"><table class="data-table">
        <thead><tr><th style="width:30px">#</th><th>Goal Title</th><th>Thrust Area</th><th>UoM</th><th>Target</th><th>Weightage</th><th v-if="canEdit || gs.sheetStatus === 'approved'">Actions</th></tr></thead>
        <tbody>
          <tr v-for="(g,i) in sortedGoals" :key="g.id">
            <td>{{ i+1 }}</td>
            <td>
              <strong style="font-size:0.875rem">{{ g.title }}</strong>
              <span v-if="g.is_shared" class="badge badge-accent" style="margin-left:6px">Shared</span>
              <p style="font-size:0.75rem;color:var(--text-muted);margin-top:2px">{{ g.description }}</p>
            </td>
            <td><span class="badge badge-default">{{ g.thrust_area }}</span></td>
            <td>{{ uomLabel(g.uom_type) }}</td>
            <td>{{ g.target_value || g.target_date || '—' }}</td>
            <td>
              <div style="display:flex;align-items:center;gap:8px">
                <div class="progress-bar" style="width:60px;height:6px"><div class="progress-fill" :style="{width:g.weightage+'%'}"></div></div>
                <span style="font-weight:600;font-size:0.85rem">{{ g.weightage }}%</span>
              </div>
            </td>
            <td v-if="canEdit || gs.sheetStatus === 'approved'">
              <div style="display:flex;gap:4px">
                <router-link v-if="canEdit" :to="`/goals/${g.id}/edit`" class="btn btn-ghost btn-sm">✏️</router-link>
                <button v-if="canEdit" class="btn btn-ghost btn-sm" @click="deleteGoal(g.id)" style="color:var(--danger)">🗑️</button>
                <router-link v-if="gs.sheetStatus === 'approved'" to="/achievements" class="btn btn-ghost btn-sm" title="Log Achievements">📊 Update</router-link>
              </div>
            </td>
          </tr>
        </tbody>
      </table></div>
    </div>

    <div v-else class="card empty-state">
      <div class="empty-state-icon">🎯</div>
      <h3>No goals created yet</h3>
      <p>Start building your goal sheet for this cycle</p>
      <router-link to="/goals/new" class="btn btn-primary" style="margin-top:16px">Create First Goal</router-link>
    </div>

    <!-- Unlock Request Modal -->
    <div v-if="showUnlockModal" class="modal-overlay" @click.self="showUnlockModal = false">
      <div class="modal">
        <div class="modal-header"><h3>Request Goal Changes</h3><button class="btn btn-ghost btn-sm" @click="showUnlockModal = false">✕</button></div>
        <div class="modal-body">
          <p style="font-size:0.9rem;color:var(--text-secondary);margin-bottom:16px">Since your goals are already approved, you must request permission from your manager to modify them.</p>
          <div class="form-group">
            <label class="form-label">Reason for changes</label>
            <textarea v-model="unlockReason" class="form-input" rows="3" placeholder="Explain why you need to edit your goals..." required></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showUnlockModal = false">Cancel</button>
          <button class="btn btn-primary" @click="requestUnlock" :disabled="!unlockReason.trim()">Submit Request</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, inject } from 'vue'
import { useGoalStore } from '../../stores/goals'

const gs = useGoalStore()
const toast = inject('toast')
const sortBy = ref('order')

onMounted(() => gs.fetchSheet())

const statusLabel = computed(() => {
  const map = { draft: '📝 Draft', submitted: '⏳ Pending Approval', approved: '✅ Approved', returned: '🔄 Returned' }
  return map[gs.sheetStatus] || '📋 Not Started'
})
const canEdit = computed(() => ['draft', 'returned', 'none'].includes(gs.sheetStatus))
const canSubmit = computed(() => ['draft', 'returned'].includes(gs.sheetStatus) && gs.totalWeightage === 100 && gs.goalCount <= 8 && gs.goalCount > 0)
const isGoalSettingOpen = computed(() => gs.windows.some(w => w.phase === 'goal_setting' && w.status === 'active'))
const sortedGoals = computed(() => {
  const g = [...gs.goals]
  if (sortBy.value === 'weightage') g.sort((a,b) => b.weightage - a.weightage)
  return g
})
function toggleSort() { sortBy.value = sortBy.value === 'weightage' ? 'order' : 'weightage' }
function uomLabel(t) {
  const map = { numeric_min:'# (Higher)', numeric_max:'# (Lower)', percent_min:'% (Higher)', percent_max:'% (Lower)', timeline:'📅 Date', zero:'0 = Success' }
  return map[t] || t
}
async function deleteGoal(id) {
  if (!confirm('Delete this goal?')) return
  try { await gs.deleteGoal(id); toast?.success('Goal deleted') } catch(e) { toast?.error(e.response?.data?.error || 'Failed') }
}
async function submitSheet() {
  if (!confirm('Submit for approval? Goals will be locked.')) return
  try { await gs.submitSheet(gs.currentSheet.id); toast?.success('Goal sheet submitted!', '🚀 Submitted') } catch(e) { toast?.error(e.response?.data?.error || 'Submit failed') }
}

const showUnlockModal = ref(false)
const unlockReason = ref('')
import api from '../../services/api'
async function requestUnlock() {
  try {
    const { data } = await api.post(`/employee/sheet/${gs.currentSheet.id}/request-unlock`, { reason: unlockReason.value })
    gs.currentSheet = data.sheet
    showUnlockModal.value = false
    toast?.success('Unlock request submitted')
  } catch(e) { toast?.error(e.response?.data?.error || 'Failed to request unlock') }
}
</script>

