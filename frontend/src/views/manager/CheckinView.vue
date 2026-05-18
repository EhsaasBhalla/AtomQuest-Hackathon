<template>
  <div>
    <div class="page-header"><h1>Check-in: {{ employee?.full_name }}</h1><p>Quarterly performance review • {{ employee?.designation }}</p></div>

    <div class="card" style="margin-bottom:20px">
      <div style="display:flex;gap:8px">
        <button v-for="q in quarters" :key="q" class="btn" :class="selectedQ===q?'btn-primary':'btn-secondary'" @click="selectedQ=q;loadCheckin()">{{ q.toUpperCase() }}</button>
      </div>
    </div>

    <!-- Planned vs Actual Chart -->
    <div class="card" style="margin-bottom:20px">
      <div class="card-header"><h3 class="card-title">📊 Planned vs Actual — {{ selectedQ.toUpperCase() }}</h3></div>
      <div style="height:220px"><canvas ref="chartRef"></canvas></div>
    </div>

    <div v-for="g in goals" :key="g.id" class="card" style="margin-bottom:16px">
      <div style="display:flex;justify-content:space-between;align-items:start">
        <div>
          <h3 style="font-size:1rem;font-weight:600">{{ g.title }}</h3>
          <div style="display:flex;gap:6px;margin-top:6px">
            <span class="badge badge-default">{{ g.thrust_area }}</span>
            <span class="badge badge-info">{{ g.weightage }}%</span>
          </div>
        </div>
        <span class="badge badge-dot" :class="g.achievement?.status==='completed'?'badge-success':g.achievement?.status==='on_track'?'badge-warning':'badge-default'">
          {{ g.achievement?.status || 'not_started' }}
        </span>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-top:16px">
        <div><div class="kpi-label">Planned Target</div><div style="font-size:1.1rem;font-weight:600">{{ g.target_value || g.target_date || '0' }}</div></div>
        <div><div class="kpi-label">Actual Achievement</div><div style="font-size:1.1rem;font-weight:600">{{ g.achievement?.actual_achievement ?? '—' }}</div></div>
        <div><div class="kpi-label">Score</div>
          <div style="font-size:1.1rem;font-weight:600" :style="{color:scoreColor(g.achievement?.computed_score)}">
            {{ g.achievement?.computed_score != null ? g.achievement.computed_score + '%' : '—' }}
          </div>
        </div>
      </div>
      <div class="progress-bar" style="margin-top:12px">
        <div class="progress-fill" :class="scoreClass(g.achievement?.computed_score)" :style="{width:(g.achievement?.computed_score||0)+'%'}"></div>
      </div>
    </div>

    <div class="card">
      <div class="card-header"><h3 class="card-title">📝 Check-in Comment</h3></div>
      <div class="form-group"><textarea v-model="comment" class="form-textarea" rows="4" placeholder="Document the check-in discussion..."></textarea></div>
      <button class="btn btn-primary" @click="saveCheckin">💾 Save Check-in</button>
      <p v-if="existingCheckin" style="margin-top:12px;font-size:0.8rem;color:var(--text-muted)">Last saved: {{ new Date(existingCheckin.checkin_date).toLocaleDateString() }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, inject } from 'vue'
import { useRoute } from 'vue-router'
import api from '../../services/api'
import { Chart, registerables } from 'chart.js'
Chart.register(...registerables)

const route = useRoute()
const toast = inject('toast')
const employee = ref(null)
const goals = ref([])
const selectedQ = ref('q1')
const comment = ref('')
const existingCheckin = ref(null)
const quarters = ['q1','q2','q3','q4']
const chartRef = ref(null)
let chartInst = null

onMounted(() => loadCheckin())

async function loadCheckin() {
  const { data } = await api.get(`/manager/team/${route.params.employeeId}/checkin/${selectedQ.value}`)
  employee.value = data.employee
  goals.value = data.goals
  existingCheckin.value = data.checkin
  comment.value = data.checkin?.manager_comment || ''
  await nextTick()
  renderChart()
}

function renderChart() {
  if (!chartRef.value || !goals.value.length) return
  if (chartInst) chartInst.destroy()
  chartInst = new Chart(chartRef.value, {
    type: 'bar',
    data: {
      labels: goals.value.map(g => g.title.substring(0,18)),
      datasets: [
        { label:'Planned', data:goals.value.map(g => g.target_value||0), backgroundColor:'rgba(79,70,229,0.2)', borderColor:'#4f46e5', borderWidth:2, borderRadius:6 },
        { label:'Actual', data:goals.value.map(g => g.achievement?.actual_achievement??0), backgroundColor:'rgba(16,185,129,0.2)', borderColor:'#10b981', borderWidth:2, borderRadius:6 }
      ]
    },
    options: { responsive:true, maintainAspectRatio:false, plugins:{ legend:{ position:'top', labels:{ usePointStyle:true, font:{ family:'Inter' } } } }, scales:{ y:{ beginAtZero:true, grid:{ color:'rgba(0,0,0,0.05)' } }, x:{ grid:{ display:false } } } }
  })
}

function scoreColor(s) { if(s==null) return 'var(--text-muted)'; if(s>=80) return 'var(--success)'; if(s>=50) return 'var(--warning)'; return 'var(--danger)' }
function scoreClass(s) { if(s>=80) return 'success'; if(s>=50) return 'warning'; return 'danger' }

async function saveCheckin() {
  const sheetId = goals.value[0]?.goal_sheet_id
  if (!sheetId) return
  try {
    await api.post('/manager/checkin', { goal_sheet_id:sheetId, quarter:selectedQ.value, comment:comment.value })
    toast?.success('Check-in saved!')
    loadCheckin()
  } catch(e) { toast?.error(e.response?.data?.error || 'Failed') }
}
</script>
