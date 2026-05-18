<template>
  <div>
    <div class="page-header"><h1>Quarterly Achievement Update</h1><p>Log your actual achievement against planned targets</p></div>

    <div class="card" style="margin-bottom:20px">
      <div style="display:flex;gap:8px">
        <button v-for="q in quarters" :key="q.key" class="btn" :class="selectedQ===q.key?'btn-primary':'btn-secondary'" @click="selectedQ=q.key">{{ q.label }}</button>
      </div>
    </div>

    <div v-if="gs.sheetStatus !== 'approved'" class="card empty-state">
      <div class="empty-state-icon">⏳</div><h3>Goals not yet approved</h3><p>Your goal sheet must be approved before logging achievements</p>
    </div>

    <div v-else>
      <!-- Chart: Planned vs Actual -->
      <div class="card" style="margin-bottom:20px">
        <div class="card-header"><h3 class="card-title">📊 Planned vs Actual — {{ selectedQ.toUpperCase() }}</h3></div>
        <div style="height:240px"><canvas ref="chartRef"></canvas></div>
      </div>

      <!-- Manager Feedback -->
      <div v-if="currentFeedback?.manager_comment" class="card" style="margin-bottom:20px; background: var(--bg-tertiary); border-left: 4px solid var(--accent);">
        <h3 style="font-size:1rem; font-weight:600; margin-bottom:8px;">💬 Manager Feedback ({{ currentFeedback.manager_name }})</h3>
        <p style="font-size:0.9rem; color:var(--text-secondary); white-space: pre-line; margin: 0;">{{ currentFeedback.manager_comment }}</p>
        <p style="font-size:0.75rem; color:var(--text-muted); margin-top:8px;">Provided on: {{ new Date(currentFeedback.checkin_date).toLocaleDateString() }}</p>
      </div>

      <!-- Window Closed Alert -->
      <div v-if="!isWindowOpen" class="card empty-state" style="margin-bottom:20px; padding: 20px; background: var(--bg-tertiary);">
        <h3 style="color: var(--text-primary); margin-bottom: 4px;">🔒 Window Closed</h3>
        <p style="color: var(--text-secondary); font-size: 0.9rem;">The {{ selectedQ.toUpperCase() }} check-in window is not currently open. You cannot save achievements right now.</p>
      </div>

      <!-- Active Goals -->
      <h3 v-if="activeGoals.length" style="margin-bottom: 12px; font-size: 1.1rem; color: var(--text-primary);">Active Goals</h3>
      <div v-for="g in activeGoals" :key="g.id" class="card" style="margin-bottom:16px">
        <div style="display:flex;justify-content:space-between;align-items:start;margin-bottom:16px">
          <div>
            <h3 style="font-size:1rem;font-weight:600">{{ g.title }}</h3>
            <div style="display:flex;gap:8px;margin-top:6px">
              <span class="badge badge-default">{{ g.thrust_area }}</span>
              <span class="badge badge-info">{{ g.weightage }}%</span>
              <span class="badge badge-accent">{{ uomLabel(g.uom_type) }}</span>
            </div>
          </div>
          <div style="text-align:right">
            <div><div class="kpi-label">Target</div><div style="font-size:1.1rem;font-weight:700">{{ g.target_value || g.target_date || '0' }}</div></div>
          </div>
        </div>
        <div v-if="achievements[g.id]" style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;align-items:end">
          <div class="form-group" style="margin:0" v-if="g.uom_type !== 'timeline'">
            <label class="form-label">Actual Achievement</label>
            <input v-model.number="achievements[g.id].actual_achievement" type="number" class="form-input" placeholder="Enter actual" :disabled="!isWindowOpen" />
          </div>
          <div class="form-group" style="margin:0" v-else>
            <label class="form-label">Completion Date</label>
            <input v-model="achievements[g.id].actual_date" type="date" class="form-input" :disabled="!isWindowOpen" />
          </div>
          <div class="form-group" style="margin:0">
            <label class="form-label">Status</label>
            <select v-model="achievements[g.id].status" class="form-select" :disabled="!isWindowOpen">
              <option value="not_started">Not Started</option><option value="on_track">On Track</option><option value="completed">Completed</option>
            </select>
          </div>
          <button class="btn btn-primary" @click="saveAchievement(g)" :disabled="!isWindowOpen">💾 Save</button>
        </div>
        <div v-if="getScore(g)" style="margin-top:12px">
          <div style="display:flex;justify-content:space-between;margin-bottom:4px">
            <span style="font-size:0.8rem;color:var(--text-muted)">Computed Score</span>
            <span style="font-size:0.85rem;font-weight:600">{{ getScore(g) }}%</span>
          </div>
          <div class="progress-bar"><div class="progress-fill" :class="scoreClass(getScore(g))" :style="{width:getScore(g)+'%'}"></div></div>
        </div>
      </div>

      <!-- Completed Goals -->
      <h3 v-if="completedGoals.length" style="margin-top: 30px; margin-bottom: 12px; font-size: 1.1rem; color: var(--success);">✅ Completed Goals</h3>
      <div v-for="g in completedGoals" :key="'comp-'+g.id" class="card" style="margin-bottom:16px; border-left: 4px solid var(--success); opacity: 0.9;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <div>
            <h3 style="font-size:1rem;font-weight:600; text-decoration: line-through; color: var(--text-secondary)">{{ g.title }}</h3>
            <div style="display:flex;gap:8px;margin-top:6px">
              <span class="badge badge-success">Completed</span>
              <span class="badge badge-info">{{ g.weightage }}%</span>
              <span class="badge badge-default">Score: {{ getScore(g) }}%</span>
            </div>
          </div>
          <div style="text-align:right">
            <div style="margin-top: 8px;">
               <button class="btn btn-secondary btn-sm" @click="achievements[g.id].status='on_track'; saveAchievement(g)" :disabled="!isWindowOpen">Reopen</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch, nextTick, inject } from 'vue'
import { useGoalStore } from '../../stores/goals'
import { Chart, registerables } from 'chart.js'
Chart.register(...registerables)

const gs = useGoalStore()
const toast = inject('toast')
const selectedQ = ref('q1')

const currentFeedback = computed(() => {
  if (!gs.currentSheet || !gs.currentSheet.checkin_records) return null
  return gs.currentSheet.checkin_records.find(c => c.quarter === selectedQ.value)
})

const isWindowOpen = computed(() => {
  if (!gs.windows || gs.windows.length === 0) return true // Fallback if no window data
  const phaseMap = { 'q1': 'q1_checkin', 'q2': 'q2_checkin', 'q3': 'q3_checkin', 'q4': 'q4_annual' }
  const phaseName = phaseMap[selectedQ.value]
  const win = gs.windows.find(w => w.phase === phaseName)
  return win ? win.is_open : false
})

const activeGoals = computed(() => {
  return gs.goals.filter(g => achievements[g.id]?.status !== 'completed')
})

const completedGoals = computed(() => {
  return gs.goals.filter(g => achievements[g.id]?.status === 'completed')
})

const achievements = reactive({})
const chartRef = ref(null)
let chartInst = null
const quarters = [{ key:'q1',label:'Q1 — Jul' },{ key:'q2',label:'Q2 — Oct' },{ key:'q3',label:'Q3 — Jan' },{ key:'q4',label:'Q4 — Annual' }]

initAchievements() // Initialize synchronously for initial render

onMounted(async () => { 
  await gs.fetchSheet()
  initAchievements() // Re-initialize after fetching fresh data
  await nextTick()
  renderChart() 
})
watch(selectedQ, () => { initAchievements(); nextTick(() => renderChart()) })

function initAchievements() {
  if (!gs.goals) return
  for (const g of gs.goals) {
    const ex = g.achievements?.find(a => a.quarter === selectedQ.value)
    achievements[g.id] = { 
      actual_achievement: ex?.actual_achievement ?? null, 
      actual_date: ex?.actual_date ?? '', 
      status: ex?.status ?? 'not_started' 
    }
  }
}

function renderChart() {
  if (!chartRef.value || !gs.goals.length) return
  if (chartInst) chartInst.destroy()
  chartInst = new Chart(chartRef.value, {
    type: 'bar',
    data: {
      labels: gs.goals.map(g => g.title.substring(0,18)),
      datasets: [
        { label:'Planned', data: gs.goals.map(g => g.target_value||0), backgroundColor:'rgba(79,70,229,0.2)', borderColor:'#4f46e5', borderWidth:2, borderRadius:6 },
        { label:'Actual', data: gs.goals.map(g => { const a=g.achievements?.find(x=>x.quarter===selectedQ.value); return a?.actual_achievement??0 }), backgroundColor:'rgba(16,185,129,0.2)', borderColor:'#10b981', borderWidth:2, borderRadius:6 }
      ]
    },
    options: { responsive:true, maintainAspectRatio:false, plugins:{ legend:{ position:'top', labels:{ usePointStyle:true, font:{ family:'Inter' } } } }, scales:{ y:{ beginAtZero:true, grid:{ color:'rgba(0,0,0,0.05)' } }, x:{ grid:{ display:false } } } }
  })
}

function uomLabel(t) { return { numeric_min:'# Higher', numeric_max:'# Lower', percent_min:'% Higher', percent_max:'% Lower', timeline:'Timeline', zero:'Zero-based' }[t] || t }
function getScore(g) { return g.achievements?.find(a => a.quarter === selectedQ.value)?.computed_score || 0 }
function scoreClass(s) { return s >= 80 ? 'success' : s >= 50 ? 'warning' : 'danger' }

async function saveAchievement(g) {
  try {
    await gs.logAchievement({ goal_id:g.id, quarter:selectedQ.value, planned_target:g.target_value, ...achievements[g.id] })
    await gs.fetchSheet(); initAchievements(); nextTick(() => renderChart())
    toast?.success('Achievement saved!')
  } catch(e) { toast?.error(e.response?.data?.error || 'Failed to save') }
}

async function deleteGoal(id) {
  if (!confirm("Are you sure you want to delete this goal? This action cannot be undone.")) return;
  try {
    await gs.deleteGoal(id)
    initAchievements(); nextTick(() => renderChart())
    toast?.success('Goal deleted successfully')
  } catch(e) {
    toast?.error(e.response?.data?.error || 'Failed to delete goal')
  }
}
</script>
