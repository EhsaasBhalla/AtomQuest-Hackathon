<template>
  <div>
    <div class="page-header" style="display:flex;justify-content:space-between;align-items:center">
      <div><h1>Reports & Export</h1><p>Achievement reports and completion tracking</p></div>
      <div style="display:flex;gap:8px">
        <button class="btn btn-secondary" @click="viewMode = viewMode==='table'?'chart':'table'">{{ viewMode==='table'?'📊 Chart View':'📋 Table View' }}</button>
        <button class="btn btn-primary" @click="exportCSV">📥 Export CSV</button>
      </div>
    </div>

    <!-- Chart View -->
    <div v-if="viewMode==='chart'" class="card" style="margin-bottom:20px">
      <div class="card-header"><h3 class="card-title">📊 Achievement Distribution</h3></div>
      <div style="height:300px"><canvas ref="chartRef"></canvas></div>
    </div>

    <!-- Table View -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">📊 Achievement Report ({{ filteredReport.length }} records)</h3>
        <div style="display:flex;gap:8px">
          <select v-model="filterQ" class="form-select" style="max-width:120px"><option value="">All Quarters</option><option v-for="q in ['Q1','Q2','Q3','Q4']" :key="q" :value="q">{{ q }}</option></select>
          <input v-model="search" class="form-input" placeholder="Search..." style="max-width:200px" />
        </div>
      </div>
      <div style="overflow-x:auto">
        <div class="table-responsive"><table class="data-table">
          <thead>
            <tr>
              <th @click="sort('employee_name')" style="cursor:pointer">Employee {{ sortIcon('employee_name') }}</th>
              <th>Department</th>
              <th @click="sort('goal_title')" style="cursor:pointer">Goal {{ sortIcon('goal_title') }}</th>
              <th>Quarter</th>
              <th @click="sort('planned_target')" style="cursor:pointer">Planned {{ sortIcon('planned_target') }}</th>
              <th @click="sort('actual_achievement')" style="cursor:pointer">Actual {{ sortIcon('actual_achievement') }}</th>
              <th @click="sort('score')" style="cursor:pointer">Score {{ sortIcon('score') }}</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(r,i) in paginatedReport" :key="i">
              <td><strong>{{ r.employee_name }}</strong></td>
              <td>{{ r.department }}</td>
              <td style="max-width:200px">{{ r.goal_title }}</td>
              <td>{{ r.quarter }}</td>
              <td>{{ r.planned_target ?? '—' }}</td>
              <td>{{ r.actual_achievement ?? '—' }}</td>
              <td><span v-if="r.score!=null" style="font-weight:600" :style="{color:scoreColor(r.score)}">{{ r.score }}%</span><span v-else style="color:var(--text-muted)">—</span></td>
              <td><span class="badge badge-dot" :class="statusBadge(r.status)">{{ r.status }}</span></td>
            </tr>
          </tbody>
        </table></div>
      </div>
      <div v-if="!filteredReport.length" class="empty-state" style="padding:24px"><div class="empty-state-icon">📄</div><h3>No data available</h3></div>
      <!-- Pagination -->
      <div v-if="totalPages > 1" style="display:flex;justify-content:center;gap:8px;margin-top:16px">
        <button class="btn btn-sm btn-secondary" :disabled="page<=1" @click="page--">← Prev</button>
        <span style="font-size:0.85rem;padding:6px 12px">Page {{ page }} of {{ totalPages }}</span>
        <button class="btn btn-sm btn-secondary" :disabled="page>=totalPages" @click="page++">Next →</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch, inject } from 'vue'
import api from '../../services/api'
import { Chart, registerables } from 'chart.js'
Chart.register(...registerables)

const toast = inject('toast')
const report = ref([])
const viewMode = ref('table')
const search = ref('')
const filterQ = ref('')
const sortKey = ref('')
const sortDir = ref('asc')
const page = ref(1)
const perPage = 15
const chartRef = ref(null)

onMounted(async () => { const { data } = await api.get('/reports/achievement'); report.value = data.report })

watch(viewMode, async (v) => { if (v === 'chart') { await nextTick(); renderChart() } })

const filteredReport = computed(() => {
  let r = report.value
  if (filterQ.value) r = r.filter(x => x.quarter === filterQ.value)
  if (search.value) { const s = search.value.toLowerCase(); r = r.filter(x => x.employee_name.toLowerCase().includes(s) || x.goal_title.toLowerCase().includes(s)) }
  if (sortKey.value) { r = [...r].sort((a,b) => { const av=a[sortKey.value]??0, bv=b[sortKey.value]??0; return sortDir.value==='asc' ? (av>bv?1:-1) : (av<bv?1:-1) }) }
  return r
})
const totalPages = computed(() => Math.max(1, Math.ceil(filteredReport.value.length / perPage)))
const paginatedReport = computed(() => filteredReport.value.slice((page.value-1)*perPage, page.value*perPage))

function sort(key) { if (sortKey.value===key) sortDir.value = sortDir.value==='asc'?'desc':'asc'; else { sortKey.value=key; sortDir.value='asc' }; page.value=1 }
function sortIcon(key) { return sortKey.value===key ? (sortDir.value==='asc'?'↑':'↓') : '↕' }
function scoreColor(s) { if(s>=80) return 'var(--success)'; if(s>=50) return 'var(--warning)'; return 'var(--danger)' }
function statusBadge(s) { return s==='completed'?'badge-success':s==='on_track'?'badge-warning':'badge-default' }

function renderChart() {
  if (!chartRef.value) return
  const byQ = {}; report.value.forEach(r => { if (!byQ[r.quarter]) byQ[r.quarter]={planned:[],actual:[]}; byQ[r.quarter].planned.push(r.planned_target||0); byQ[r.quarter].actual.push(r.actual_achievement||0) })
  const labels = Object.keys(byQ)
  new Chart(chartRef.value, {
    type:'bar',
    data: { labels, datasets:[
      { label:'Avg Planned', data:labels.map(q => { const a=byQ[q].planned; return a.length?Math.round(a.reduce((s,v)=>s+v,0)/a.length):0 }), backgroundColor:'rgba(79,70,229,0.2)', borderColor:'#4f46e5', borderWidth:2, borderRadius:6 },
      { label:'Avg Actual', data:labels.map(q => { const a=byQ[q].actual; return a.length?Math.round(a.reduce((s,v)=>s+v,0)/a.length):0 }), backgroundColor:'rgba(16,185,129,0.2)', borderColor:'#10b981', borderWidth:2, borderRadius:6 },
    ]},
    options:{ responsive:true, maintainAspectRatio:false, plugins:{ legend:{ position:'top', labels:{ usePointStyle:true } } }, scales:{ y:{ beginAtZero:true }, x:{ grid:{ display:false } } } }
  })
}

async function exportCSV() {
  try {
    const res = await api.get('/reports/achievement', { params:{format:'csv'}, responseType:'blob' })
    const url = URL.createObjectURL(new Blob([res.data]))
    const a = document.createElement('a'); a.href=url; a.download='achievement_report.csv'; a.click(); URL.revokeObjectURL(url)
    toast?.success('Report exported!')
  } catch(e) { toast?.error('Export failed') }
}
</script>

