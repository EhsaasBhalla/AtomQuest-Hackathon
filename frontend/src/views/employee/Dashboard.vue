<template>
  <div>
    <div class="page-header">
      <h1>Welcome back, {{ auth.user?.full_name?.split(' ')[0] }} 👋</h1>
      <p>Track your goals, monitor progress, and stay aligned with organizational priorities.</p>
    </div>

    <!-- Loading skeleton -->
    <div v-if="goalStore.loading" class="kpi-grid">
      <div v-for="i in 4" :key="i" class="kpi-card"><div class="skeleton skeleton-card"></div></div>
    </div>

    <!-- KPI Cards -->
    <div v-else class="kpi-grid">
      <div class="kpi-card info">
        <div class="kpi-icon">🎯</div>
        <div class="kpi-label">Total Goals</div>
        <div class="kpi-value">{{ goalStore.goalCount }}</div>
        <div class="kpi-change">FY 2026-27</div>
      </div>
      <div class="kpi-card" :class="weightClass">
        <div class="kpi-icon">⚖️</div>
        <div class="kpi-label">Weightage Used</div>
        <div class="kpi-value">{{ goalStore.totalWeightage }}%</div>
        <div class="kpi-change" :class="goalStore.totalWeightage === 100 ? 'positive' : 'negative'">
          {{ goalStore.remainingWeightage }}% remaining
        </div>
      </div>
      <div class="kpi-card success">
        <div class="kpi-icon">📊</div>
        <div class="kpi-label">Sheet Status</div>
        <div class="kpi-value" style="font-size:1.3rem">
          <span class="badge" :class="statusBadgeClass">{{ statusLabel }}</span>
        </div>
      </div>
      <div class="kpi-card warning">
        <div class="kpi-icon">📈</div>
        <div class="kpi-label">Avg Score</div>
        <div class="kpi-value">{{ avgScore }}%</div>
        <div class="kpi-change">Latest Quarter</div>
      </div>
    </div>

    <!-- Charts + Quick Actions Row -->
    <div class="dashboard-grid">
      <!-- Goal Progress Chart -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">📊 Goal Progress Overview</h3>
        </div>
        <div v-if="goalStore.goals.length" class="chart-container">
          <canvas ref="progressChart"></canvas>
        </div>
        <div v-else class="empty-state" style="padding:24px">
          <div class="empty-state-icon">📊</div>
          <h3>No data yet</h3>
          <p>Create goals to see progress charts</p>
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">⚡ Quick Actions</h3>
        </div>
        <div class="quick-actions">
          <router-link to="/goals" class="action-card">
            <span class="action-icon">🎯</span>
            <div>
              <strong>My Goal Sheet</strong>
              <p>View and manage your goals</p>
            </div>
            <span class="action-arrow">→</span>
          </router-link>
          <router-link to="/goals/new" class="action-card" v-if="canAddGoals">
            <span class="action-icon">➕</span>
            <div>
              <strong>Add New Goal</strong>
              <p>Create a new goal entry</p>
            </div>
            <span class="action-arrow">→</span>
          </router-link>
          <router-link to="/achievements" class="action-card">
            <span class="action-icon">📈</span>
            <div>
              <strong>Update Achievements</strong>
              <p>Log quarterly progress</p>
            </div>
            <span class="action-arrow">→</span>
          </router-link>
          <router-link v-if="auth.userRole === 'manager' || auth.userRole === 'admin'" to="/team" class="action-card">
            <span class="action-icon">👥</span>
            <div>
              <strong>Team Dashboard</strong>
              <p>Review team performance</p>
            </div>
            <span class="action-arrow">→</span>
          </router-link>
        </div>
      </div>
    </div>

    <!-- Goal Details List -->
    <div class="card" style="margin-top:20px">
      <div class="card-header">
        <h3 class="card-title">🎯 Goal Progress Detail</h3>
        <router-link to="/goals" class="btn btn-secondary btn-sm">View All →</router-link>
      </div>
      <div v-if="goalStore.goals.length" class="goals-mini">
        <div v-for="g in goalStore.goals" :key="g.id" class="goal-mini-item">
          <div class="goal-mini-top">
            <div>
              <span class="goal-mini-title">{{ g.title }}</span>
              <span class="badge badge-default" style="margin-left:8px">{{ g.thrust_area }}</span>
            </div>
            <div style="display:flex;align-items:center;gap:10px">
              <span class="badge badge-info">{{ g.weightage }}%</span>
              <span style="font-size:0.85rem;font-weight:600;min-width:40px;text-align:right"
                :style="{ color: scoreColor(goalScore(g)) }">
                {{ goalScore(g) }}%
              </span>
            </div>
          </div>
          <div class="progress-bar" style="height:6px">
            <div class="progress-fill" :class="scoreClass(goalScore(g))"
              :style="{ width: goalScore(g) + '%' }"></div>
          </div>
        </div>
      </div>
      <div v-else class="empty-state">
        <div class="empty-state-icon">📋</div>
        <h3>No goals yet</h3>
        <p>Create your goal sheet to get started</p>
        <router-link to="/goals" class="btn btn-primary" style="margin-top:12px">Get Started</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch, nextTick } from 'vue'
import { useAuthStore } from '../../stores/auth'
import { useGoalStore } from '../../stores/goals'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

const auth = useAuthStore()
const goalStore = useGoalStore()
const progressChart = ref(null)
let chartInstance = null

onMounted(async () => {
  await goalStore.fetchSheet()
  await nextTick()
  renderChart()
})

watch(() => goalStore.goals, () => {
  nextTick(() => renderChart())
}, { deep: true })

function renderChart() {
  if (!progressChart.value || !goalStore.goals.length) return
  if (chartInstance) chartInstance.destroy()

  const labels = goalStore.goals.map(g => g.title.substring(0, 20) + (g.title.length > 20 ? '…' : ''))
  const targets = goalStore.goals.map(g => g.target_value || 100)
  const actuals = goalStore.goals.map(g => {
    const a = g.achievements?.find(a => a.quarter === 'q1')
    return a?.actual_achievement ?? 0
  })

  chartInstance = new Chart(progressChart.value, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: 'Target',
          data: targets,
          backgroundColor: 'rgba(79, 70, 229, 0.15)',
          borderColor: '#4f46e5',
          borderWidth: 2,
          borderRadius: 6,
          barPercentage: 0.6,
        },
        {
          label: 'Actual',
          data: actuals,
          backgroundColor: 'rgba(16, 185, 129, 0.2)',
          borderColor: '#10b981',
          borderWidth: 2,
          borderRadius: 6,
          barPercentage: 0.6,
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'top', labels: { usePointStyle: true, padding: 20, font: { family: 'Inter', size: 12 } } },
      },
      scales: {
        y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.05)' }, ticks: { font: { family: 'Inter', size: 11 } } },
        x: { grid: { display: false }, ticks: { font: { family: 'Inter', size: 11 } } },
      }
    }
  })
}

const statusLabel = computed(() => {
  const map = { draft: 'Draft', submitted: 'Pending Review', approved: 'Approved', returned: 'Returned', none: 'Not Started' }
  return map[goalStore.sheetStatus] || 'Not Started'
})

const statusBadgeClass = computed(() => {
  const map = { draft: 'badge-default', submitted: 'badge-warning', approved: 'badge-success', returned: 'badge-danger' }
  return map[goalStore.sheetStatus] || 'badge-default'
})

const weightClass = computed(() => {
  if (goalStore.totalWeightage === 100) return 'success'
  if (goalStore.totalWeightage > 0) return 'warning'
  return 'info'
})

const canAddGoals = computed(() => ['draft', 'returned', 'none'].includes(goalStore.sheetStatus))

function goalScore(g) {
  if (!g.achievements?.length) return 0
  const latest = g.achievements[g.achievements.length - 1]
  return latest.computed_score || 0
}

function scoreClass(s) {
  if (s >= 80) return 'success'
  if (s >= 50) return 'warning'
  return 'danger'
}

function scoreColor(s) {
  if (s >= 80) return 'var(--success)'
  if (s >= 50) return 'var(--warning)'
  if (s > 0) return 'var(--danger)'
  return 'var(--text-muted)'
}

const avgScore = computed(() => {
  const scores = goalStore.goals.map(g => goalScore(g)).filter(s => s > 0)
  if (!scores.length) return 0
  return Math.round(scores.reduce((a, b) => a + b, 0) / scores.length)
})
</script>

<style scoped>
.dashboard-grid {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 20px;
}

.chart-container {
  height: 280px;
  position: relative;
}

.kpi-icon {
  font-size: 1.5rem;
  margin-bottom: 4px;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.action-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-light);
  text-decoration: none;
  color: var(--text-primary);
  transition: var(--transition);
}

.action-card:hover {
  background: var(--bg-tertiary);
  border-color: var(--accent);
  transform: translateX(4px);
}

.action-icon { font-size: 1.4rem; flex-shrink: 0; }
.action-card strong { font-size: 0.9rem; display: block; }
.action-card p { font-size: 0.75rem; color: var(--text-muted); margin: 2px 0 0; }
.action-arrow { margin-left: auto; color: var(--text-muted); font-size: 1.1rem; }

.goals-mini {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.goal-mini-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.goal-mini-title {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--text-primary);
}

@media (max-width: 1024px) {
  .dashboard-grid { grid-template-columns: 1fr; }
}
</style>
