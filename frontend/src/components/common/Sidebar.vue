<template>
  <aside class="sidebar-wrapper">
    <div v-if="!collapsed" class="mobile-overlay" @click="$emit('toggle')"></div>
    <div class="sidebar" :class="{ collapsed }">
    <div class="sidebar-header">
      <div class="logo-area">
        <div class="logo-icon">⚡</div>
        <transition name="fade"><span v-if="!collapsed" class="logo-text">GoalTracker</span></transition>
      </div>
      <button class="collapse-btn" @click="$emit('toggle')" :title="collapsed ? 'Expand' : 'Collapse'">
        <span>{{ collapsed ? '▸' : '◂' }}</span>
      </button>
    </div>

    <nav class="sidebar-nav">
      <div class="nav-section">
        <span v-if="!collapsed" class="nav-section-title">Main</span>
        <router-link to="/dashboard" class="nav-item" active-class="active" title="Dashboard"><span class="nav-icon">📊</span><span v-if="!collapsed" class="nav-label">Dashboard</span></router-link>
        <router-link to="/goals" class="nav-item" active-class="active" title="My Goals"><span class="nav-icon">🎯</span><span v-if="!collapsed" class="nav-label">My Goals</span></router-link>
        <router-link to="/achievements" class="nav-item" active-class="active" title="Quarterly Update"><span class="nav-icon">📈</span><span v-if="!collapsed" class="nav-label">Quarterly Update</span></router-link>
      </div>

      <div v-if="showManagerNav" class="nav-section">
        <span v-if="!collapsed" class="nav-section-title">Manager</span>
        <router-link to="/team" class="nav-item" active-class="active" title="My Team"><span class="nav-icon">👥</span><span v-if="!collapsed" class="nav-label">My Team</span></router-link>
        <router-link to="/admin/shared-goals" class="nav-item" active-class="active" title="Shared Goals"><span class="nav-icon">🔗</span><span v-if="!collapsed" class="nav-label">Shared Goals</span></router-link>
      </div>

      <div v-if="showAdminNav" class="nav-section">
        <span v-if="!collapsed" class="nav-section-title">Admin</span>
        <router-link to="/admin" class="nav-item" active-class="active" title="Admin Dashboard"><span class="nav-icon">⚙️</span><span v-if="!collapsed" class="nav-label">Admin Panel</span></router-link>
        <router-link to="/admin/cycles" class="nav-item" active-class="active" title="Cycles"><span class="nav-icon">🔄</span><span v-if="!collapsed" class="nav-label">Cycles</span></router-link>
        <router-link to="/admin/users" class="nav-item" active-class="active" title="Users"><span class="nav-icon">👤</span><span v-if="!collapsed" class="nav-label">Users</span></router-link>
        <router-link to="/admin/audit" class="nav-item" active-class="active" title="Audit Logs"><span class="nav-icon">📋</span><span v-if="!collapsed" class="nav-label">Audit Logs</span></router-link>
        <router-link to="/admin/reports" class="nav-item" active-class="active" title="Reports"><span class="nav-icon">📄</span><span v-if="!collapsed" class="nav-label">Reports</span></router-link>
        <router-link to="/admin/escalations" class="nav-item" active-class="active" title="Escalations"><span class="nav-icon">⚠️</span><span v-if="!collapsed" class="nav-label">Escalations</span></router-link>
      </div>
    </nav>

    <div class="sidebar-footer">

    </div>
      </div>
    <!-- </div> -->
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { useAuthStore } from '../../stores/auth'
import { useRouter } from 'vue-router'

defineProps({ collapsed: Boolean })
defineEmits(['toggle'])

const auth = useAuthStore()
const router = useRouter()
const role = computed(() => auth.userRole)
const showManagerNav = computed(() => ['manager', 'admin'].includes(role.value))
const showAdminNav = computed(() => role.value === 'admin')

async function switchRole(r) {
  try { await auth.switchRole(r); router.push('/dashboard') }
  catch(e) { console.error('Role switch failed', e) }
}
</script>

<style scoped>
.sidebar { position:fixed; left:0; top:0; bottom:0; width:var(--sidebar-width); background:var(--bg-secondary); border-right:1px solid var(--border); display:flex; flex-direction:column; transition:width 0.3s cubic-bezier(0.4,0,0.2,1); z-index:100; overflow:hidden; }
.sidebar.collapsed { width:var(--sidebar-collapsed); }
.sidebar-header { display:flex; align-items:center; justify-content:space-between; padding:16px; border-bottom:1px solid var(--border-light); min-height:var(--navbar-height); }
.logo-area { display:flex; align-items:center; gap:10px; overflow:hidden; }
.logo-icon { width:36px; height:36px; background:linear-gradient(135deg,var(--accent),#7c3aed); border-radius:var(--radius-md); display:flex; align-items:center; justify-content:center; font-size:1.1rem; flex-shrink:0; }
.logo-text { font-size:1.1rem; font-weight:700; color:var(--text-primary); white-space:nowrap; letter-spacing:-0.02em; }
.collapse-btn { background:none; border:none; color:var(--text-muted); cursor:pointer; padding:4px; border-radius:var(--radius-sm); transition:var(--transition); flex-shrink:0; }
.collapse-btn:hover { background:var(--bg-tertiary); color:var(--text-primary); }
.sidebar-nav { flex:1; padding:12px 8px; overflow-y:auto; }
.nav-section { margin-bottom:16px; }
.nav-section-title { display:block; font-size:0.65rem; font-weight:600; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.08em; padding:4px 12px; margin-bottom:4px; }
.nav-item { display:flex; align-items:center; gap:10px; padding:9px 12px; border-radius:var(--radius-md); color:var(--text-secondary); text-decoration:none; font-size:0.875rem; font-weight:500; transition:var(--transition); white-space:nowrap; margin-bottom:2px; }
.nav-item:hover { background:var(--bg-tertiary); color:var(--text-primary); }
.nav-item.active { background:var(--accent-bg); color:var(--accent); }
.nav-icon { font-size:1.1rem; width:24px; text-align:center; flex-shrink:0; }
.sidebar-footer { padding:12px; border-top:1px solid var(--border-light); }
.role-buttons { display:flex; gap:4px; margin-top:6px; }
.role-btn { flex:1; padding:6px 4px; border:1px solid var(--border); border-radius:var(--radius-sm); background:var(--bg-tertiary); color:var(--text-secondary); font-size:0.7rem; font-weight:500; cursor:pointer; transition:var(--transition); }
.role-btn:hover { background:var(--border); }
.role-btn.active { background:var(--accent); color:white; border-color:var(--accent); }

.mobile-overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 90; backdrop-filter: blur(2px); }

@media (max-width: 768px) {
  .sidebar { transform: translateX(-100%); transition: transform 0.3s ease; }
  .sidebar:not(.collapsed) { transform: translateX(0); width: var(--sidebar-width); }
  .mobile-overlay { display: block; }
  .collapse-btn { display: none; }
}
</style>
