<template>
  <div>
    <div class="page-header"><h1>Admin Dashboard</h1><p>Organization-wide goal completion and performance oversight</p></div>

    <div v-if="loading" class="kpi-grid"><div v-for="i in 4" :key="i" class="kpi-card"><div class="skeleton skeleton-card"></div></div></div>
    <div v-else class="kpi-grid">
      <div class="kpi-card info"><div class="kpi-icon">👥</div><div class="kpi-label">Total Employees</div><div class="kpi-value">{{ stats.total_employees }}</div></div>
      <div class="kpi-card success"><div class="kpi-icon">✅</div><div class="kpi-label">Sheets Approved</div><div class="kpi-value">{{ stats.approved }}</div></div>
      <div class="kpi-card warning"><div class="kpi-icon">⏳</div><div class="kpi-label">Pending Approval</div><div class="kpi-value">{{ stats.submitted }}</div></div>
      <div class="kpi-card danger"><div class="kpi-icon">🚫</div><div class="kpi-label">Not Started</div><div class="kpi-value">{{ stats.not_started }}</div></div>
    </div>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px">
      <!-- Completion Donut -->
      <div class="card">
        <div class="card-header"><h3 class="card-title">📊 Goal Sheet Completion</h3></div>
        <div style="height:240px;display:flex;align-items:center;justify-content:center"><canvas ref="donutRef"></canvas></div>
      </div>
      <!-- QoQ Trend -->
      <div class="card">
        <div class="card-header"><h3 class="card-title">📈 Quarter-on-Quarter Trends</h3></div>
        <div style="height:240px"><canvas ref="trendRef"></canvas></div>
      </div>
    </div>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px">
      <div class="card">
        <div class="card-header"><h3 class="card-title">📋 Quarterly Check-in Status</h3></div>
        <div class="table-responsive"><table class="data-table">
          <thead><tr><th>Quarter</th><th>Achievements</th><th>Check-ins</th></tr></thead>
          <tbody>
            <tr v-for="q in ['q1','q2','q3','q4']" :key="q">
              <td><strong>{{ q.toUpperCase() }}</strong></td>
              <td>{{ stats[q+'_achievements'] || 0 }} entries</td>
              <td>{{ stats[q+'_checkins'] || 0 }} completed</td>
            </tr>
          </tbody>
        </table></div>
      </div>

      <div class="card">
        <div class="card-header"><h3 class="card-title">🔥 Quick Links</h3></div>
        <div style="display:flex;flex-direction:column;gap:8px">
          <router-link to="/admin/cycles" class="action-link">🔄 Manage Cycles</router-link>
          <router-link to="/admin/users" class="action-link">👤 User Management</router-link>
          <router-link to="/admin/audit" class="action-link">📋 Audit Logs</router-link>
          <router-link to="/admin/reports" class="action-link">📄 Reports & Export</router-link>
          <router-link to="/admin/shared-goals" class="action-link">🎯 Shared Goals</router-link>
          <router-link to="/admin/escalations" class="action-link">⚠️ Escalation Rules</router-link>
        </div>
      </div>
    </div>

    <!-- Department Table -->
    <div class="card">
      <div class="card-header"><h3 class="card-title">🏢 Department Overview</h3><router-link to="/admin/reports" class="btn btn-secondary btn-sm">View Reports →</router-link></div>
      <div class="table-responsive"><table class="data-table">
        <thead><tr><th>Department</th><th>Employees</th><th>Approved</th><th>Submitted</th><th>Completion Rate</th></tr></thead>
        <tbody>
          <tr v-for="d in deptStats" :key="d.department">
            <td><strong>{{ d.department }}</strong></td>
            <td>{{ d.total_employees }}</td>
            <td><span class="badge badge-success">{{ d.sheets_approved }}</span></td>
            <td><span class="badge badge-warning">{{ d.sheets_submitted }}</span></td>
            <td>
              <div style="display:flex;align-items:center;gap:8px">
                <div class="progress-bar" style="width:100px;height:6px"><div class="progress-fill success" :style="{width:deptPct(d)+'%'}"></div></div>
                <span style="font-size:0.8rem;font-weight:600">{{ deptPct(d) }}%</span>
              </div>
            </td>
          </tr>
        </tbody>
      </table></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import api from '../../services/api'
import { Chart, registerables } from 'chart.js'
Chart.register(...registerables)

const stats = ref({})
const deptStats = ref([])
const qoq = ref({})
const loading = ref(true)
const donutRef = ref(null)
const trendRef = ref(null)

onMounted(async () => {
  try {
    const [dash, analytics] = await Promise.all([api.get('/admin/completion-dashboard'), api.get('/admin/analytics/overview')])
    stats.value = dash.data.stats
    deptStats.value = analytics.data.departments
    qoq.value = analytics.data.qoq
  } finally { loading.value = false }
  await nextTick()
  renderDonut()
  renderTrend()
})

function renderDonut() {
  if (!donutRef.value) return
  const s = stats.value
  new Chart(donutRef.value, {
    type: 'doughnut',
    data: {
      labels: ['Approved','Submitted','Draft','Not Started'],
      datasets: [{ data: [s.approved||0, s.submitted||0, s.draft||0, s.not_started||0], backgroundColor: ['#10b981','#f59e0b','#94a3b8','#ef4444'], borderWidth: 0, borderRadius: 4 }]
    },
    options: { responsive:true, maintainAspectRatio:false, cutout:'65%', plugins:{ legend:{ position:'bottom', labels:{ usePointStyle:true, padding:16, font:{ family:'Inter', size:12 } } } } }
  })
}

function renderTrend() {
  if (!trendRef.value || !qoq.value) return
  new Chart(trendRef.value, {
    type: 'line',
    data: {
      labels: ['Q1','Q2','Q3','Q4'],
      datasets: [
        { label:'Avg Score', data: ['q1','q2','q3','q4'].map(q => qoq.value[q]?.avg_score||0), borderColor:'#4f46e5', backgroundColor:'rgba(79,70,229,0.1)', fill:true, tension:0.4, pointRadius:5, pointBackgroundColor:'#4f46e5' },
        { label:'Completed', data: ['q1','q2','q3','q4'].map(q => qoq.value[q]?.completed||0), borderColor:'#10b981', backgroundColor:'rgba(16,185,129,0.1)', fill:true, tension:0.4, pointRadius:5, pointBackgroundColor:'#10b981' }
      ]
    },
    options: { responsive:true, maintainAspectRatio:false, plugins:{ legend:{ position:'top', labels:{ usePointStyle:true, font:{ family:'Inter' } } } }, scales:{ y:{ beginAtZero:true, grid:{ color:'rgba(0,0,0,0.05)' } }, x:{ grid:{ display:false } } } }
  })
}

function deptPct(d) { return d.total_employees ? Math.round((d.sheets_approved/d.total_employees)*100) : 0 }
</script>

<style scoped>
.kpi-icon { font-size:1.3rem; margin-bottom:2px; }
.action-link { display:flex; align-items:center; gap:8px; padding:10px 14px; border-radius:var(--radius-md); border:1px solid var(--border-light); text-decoration:none; color:var(--text-primary); font-size:0.875rem; font-weight:500; transition:var(--transition); }
.action-link:hover { background:var(--bg-tertiary); border-color:var(--accent); transform:translateX(4px); }
</style>

