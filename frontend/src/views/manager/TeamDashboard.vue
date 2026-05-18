<template>
  <div>
    <div class="page-header"><h1>My Team</h1><p>Review goal sheets, approve submissions, and conduct quarterly check-ins</p></div>

    <div v-if="loading" class="kpi-grid"><div v-for="i in 4" :key="i" class="kpi-card"><div class="skeleton skeleton-card"></div></div></div>

    <div v-else class="kpi-grid">
      <div class="kpi-card info"><div class="kpi-icon">👥</div><div class="kpi-label">Direct Reports</div><div class="kpi-value">{{ team.length }}</div></div>
      <div class="kpi-card warning"><div class="kpi-icon">⏳</div><div class="kpi-label">Pending Approval</div><div class="kpi-value">{{ pending }}</div></div>
      <div class="kpi-card success"><div class="kpi-icon">✅</div><div class="kpi-label">Approved</div><div class="kpi-value">{{ approved }}</div></div>
      <div class="kpi-card danger"><div class="kpi-icon">🚫</div><div class="kpi-label">Not Started</div><div class="kpi-value">{{ notStarted }}</div></div>
    </div>

    <!-- Team Progress Heatmap -->
    <div class="card" style="margin-bottom:20px">
      <div class="card-header"><h3 class="card-title">🗓️ Team Progress Heatmap</h3></div>
      <div class="heatmap-container">
        <table class="heatmap-table">
          <thead><tr><th>Employee</th><th>Goal Sheet</th><th>Q1</th><th>Q2</th><th>Q3</th><th>Q4</th></tr></thead>
          <tbody>
            <tr v-for="m in team" :key="m.id">
              <td>
                <div style="display:flex;align-items:center;gap:8px">
                  <div class="avatar avatar-sm" :style="{background:m.avatar_color}">{{ initials(m.full_name) }}</div>
                  <span style="font-size:0.82rem;font-weight:500">{{ m.full_name }}</span>
                </div>
              </td>
              <td><div class="heat-cell" :class="heatClass(m.goal_sheet_status)">{{ statusShort(m.goal_sheet_status) }}</div></td>
              <td v-for="q in ['q1','q2','q3','q4']" :key="q">
                <div class="heat-cell" :class="checkinHeat(m, q)">{{ checkinLabel(m, q) }}</div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Team Table -->
    <div class="card">
      <div class="card-header"><h3 class="card-title">Team Members</h3></div>
      <div class="table-responsive"><table class="data-table">
        <thead><tr><th>Employee</th><th>Department</th><th>Goal Sheet Status</th><th>Goals</th><th>Actions</th></tr></thead>
        <tbody>
          <tr v-for="m in team" :key="m.id">
            <td>
              <div style="display:flex;align-items:center;gap:10px">
                <div class="avatar" :style="{background:m.avatar_color}">{{ initials(m.full_name) }}</div>
                <div><strong style="font-size:0.875rem">{{ m.full_name }}</strong><div style="font-size:0.75rem;color:var(--text-muted)">{{ m.email }}</div></div>
              </div>
            </td>
            <td>{{ m.department_name || '—' }}</td>
            <td>
              <span class="badge badge-dot" :class="statusBadge(m.goal_sheet_status)">{{ statusLabel(m.goal_sheet_status) }}</span>
              <span v-if="m.goal_sheet?.unlock_requested" class="badge badge-info" style="margin-left:8px;font-size:0.7rem">🔓 Unlock Requested</span>
            </td>
            <td>{{ m.goal_sheet?.goal_count || 0 }}</td>
            <td>
              <div style="display:flex;gap:4px">
                <router-link v-if="m.goal_sheet" :to="`/team/${m.id}/review`" class="btn btn-sm btn-secondary">{{ m.goal_sheet_status==='submitted'?'✅ Review':'👁️ View' }}</router-link>
                <router-link v-if="m.goal_sheet_status==='approved'" :to="`/team/${m.id}/checkin`" class="btn btn-sm btn-primary">📝 Check-in</router-link>
              </div>
            </td>
          </tr>
        </tbody>
      </table></div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../../services/api'

const team = ref([])
const loading = ref(true)

onMounted(async () => {
  try { const { data } = await api.get('/manager/team'); team.value = data.team } finally { loading.value = false }
})

const pending = computed(() => team.value.filter(m => m.goal_sheet_status === 'submitted').length)
const approved = computed(() => team.value.filter(m => m.goal_sheet_status === 'approved').length)
const notStarted = computed(() => team.value.filter(m => m.goal_sheet_status === 'not_started').length)

function initials(n) { return n?.split(' ').map(w => w[0]).join('').toUpperCase() || '?' }
function statusBadge(s) { return { draft:'badge-default', submitted:'badge-warning', approved:'badge-success', returned:'badge-danger', not_started:'badge-default' }[s] || 'badge-default' }
function statusLabel(s) { return { draft:'Draft', submitted:'Pending Review', approved:'Approved', returned:'Returned', not_started:'Not Started' }[s] || 'Not Started' }
function statusShort(s) { return { draft:'DRF', submitted:'SUB', approved:'APR', returned:'RET', not_started:'—' }[s] || '—' }
function heatClass(s) { return { approved:'heat-green', submitted:'heat-yellow', draft:'heat-gray', returned:'heat-red', not_started:'heat-empty' }[s] || 'heat-empty' }
function checkinHeat(m, q) { return 'heat-empty' }
function checkinLabel(m, q) { return '—' }
</script>

<style scoped>
.kpi-icon { font-size:1.3rem; margin-bottom:2px; }
.avatar-sm { width:28px; height:28px; font-size:0.65rem; }
.heatmap-container { overflow-x:auto; }
.heatmap-table { width:100%; border-collapse:collapse; }
.heatmap-table th { text-align:left; padding:8px 12px; font-size:0.72rem; font-weight:600; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.05em; }
.heatmap-table td { padding:6px 12px; }
.heat-cell { display:inline-block; padding:4px 10px; border-radius:6px; font-size:0.72rem; font-weight:600; text-align:center; min-width:42px; }
.heat-green { background:#dcfce7; color:#16a34a; }
.heat-yellow { background:#fef9c3; color:#a16207; }
.heat-red { background:#fecaca; color:#dc2626; }
.heat-gray { background:var(--bg-tertiary); color:var(--text-muted); }
.heat-empty { background:var(--bg-tertiary); color:var(--text-muted); }
</style>

