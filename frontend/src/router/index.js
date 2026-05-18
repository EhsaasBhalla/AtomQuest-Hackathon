import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue'), meta: { public: true } },
  { path: '/signup', name: 'Signup', component: () => import('../views/Signup.vue'), meta: { public: true } },
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', name: 'Dashboard', component: () => import('../views/employee/Dashboard.vue') },
  { path: '/goals', name: 'GoalSheet', component: () => import('../views/employee/GoalSheet.vue') },
  { path: '/goals/new', name: 'GoalForm', component: () => import('../views/employee/GoalForm.vue') },
  { path: '/goals/:id/edit', name: 'GoalEdit', component: () => import('../views/employee/GoalForm.vue'), props: true },
  { path: '/achievements', name: 'QuarterlyUpdate', component: () => import('../views/employee/QuarterlyUpdate.vue') },
  // Manager routes
  { path: '/team', name: 'TeamDashboard', component: () => import('../views/manager/TeamDashboard.vue'), meta: { roles: ['manager', 'admin'] } },
  { path: '/team/:employeeId/review', name: 'ApprovalView', component: () => import('../views/manager/ApprovalView.vue'), meta: { roles: ['manager', 'admin'] }, props: true },
  { path: '/team/:employeeId/checkin', name: 'CheckinView', component: () => import('../views/manager/CheckinView.vue'), meta: { roles: ['manager', 'admin'] }, props: true },
  // Admin routes
  { path: '/admin', name: 'AdminDashboard', component: () => import('../views/admin/AdminDashboard.vue'), meta: { roles: ['admin'] } },
  { path: '/admin/cycles', name: 'CycleManager', component: () => import('../views/admin/CycleManager.vue'), meta: { roles: ['admin'] } },
  { path: '/admin/users', name: 'UserManager', component: () => import('../views/admin/UserManager.vue'), meta: { roles: ['admin'] } },
  { path: '/admin/audit', name: 'AuditLogs', component: () => import('../views/admin/AuditLogs.vue'), meta: { roles: ['admin'] } },
  { path: '/admin/reports', name: 'Reports', component: () => import('../views/admin/Reports.vue'), meta: { roles: ['admin', 'manager'] } },
  { path: '/admin/shared-goals', name: 'SharedGoals', component: () => import('../views/admin/SharedGoals.vue'), meta: { roles: ['admin', 'manager'] } },
  { path: '/admin/escalations', name: 'EscalationManager', component: () => import('../views/admin/EscalationManager.vue'), meta: { roles: ['admin'] } },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token')
  const user = JSON.parse(localStorage.getItem('user') || 'null')
  if (!to.meta.public && !token) return next('/login')
  if (to.meta.roles && user && !to.meta.roles.includes(user.role)) return next('/dashboard')
  next()
})

export default router
