<template>
  <div>
    <div class="page-header" style="display:flex;justify-content:space-between;align-items:center">
      <div><h1>User Management</h1><p>Manage employees, managers, and org hierarchy</p></div>
      <button class="btn btn-primary" @click="showModal = true">➕ Add User</button>
    </div>
    <div class="card">
      <div style="margin-bottom:16px;display:flex;gap:8px">
        <input v-model="search" class="form-input" placeholder="Search users..." style="max-width:300px" />
        <select v-model="filterRole" class="form-select" style="max-width:160px">
          <option value="">All Roles</option>
          <option value="employee">Employee</option>
          <option value="manager">Manager</option>
          <option value="admin">Admin</option>
        </select>
      </div>
      <div class="table-responsive"><table class="data-table">
        <thead><tr><th>User</th><th>Email</th><th>Role</th><th>Department</th><th>Manager</th><th>Status</th></tr></thead>
        <tbody>
          <tr v-for="u in filteredUsers" :key="u.id" :class="{'inactive-row': !u.is_active}">
            <td>
              <div style="display:flex;align-items:center;gap:10px;cursor:pointer" @click="openProfile(u)">
                <div class="avatar" :style="{ background: u.is_active ? u.avatar_color : '#ccc' }">{{ initials(u.full_name) }}</div>
                <strong style="color:var(--accent);text-decoration:underline">{{ u.full_name }}</strong>
              </div>
            </td>
            <td style="font-size:0.8rem;color:var(--text-muted)">{{ u.email }}</td>
            <td><span class="badge" :class="u.role==='admin'?'badge-accent':u.role==='manager'?'badge-info':'badge-default'">{{ u.role }}</span></td>
            <td>{{ u.department_name || '—' }}</td>
            <td>{{ u.manager_name || '—' }}</td>
            <td><span class="badge badge-dot" :class="u.is_active ? 'badge-success' : 'badge-danger'">{{ u.is_active ? 'Active' : 'Inactive' }}</span></td>
          </tr>
        </tbody>
      </table></div>
    </div>

    <!-- User Profile Modal -->
    <div v-if="selectedUser" class="modal-overlay" @click.self="selectedUser = null">
      <div class="modal" style="max-width:500px">
        <div class="modal-header">
          <h3>User Profile</h3>
          <button class="btn btn-ghost btn-sm" @click="selectedUser = null">✕</button>
        </div>
        <div class="modal-body" style="text-align:center">
          <div class="avatar" :style="{ background: selectedUser.is_active ? selectedUser.avatar_color : '#ccc', width:'80px', height:'80px', fontSize:'2rem', margin:'0 auto 16px' }">
            {{ initials(selectedUser.full_name) }}
          </div>
          <h2 style="font-size:1.5rem;margin-bottom:4px">{{ selectedUser.full_name }}</h2>
          <p style="color:var(--text-muted);font-size:0.9rem;margin-bottom:16px">{{ selectedUser.email }}</p>
          
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;text-align:left;background:var(--bg-secondary);padding:16px;border-radius:var(--radius-md);margin-bottom:24px">
            <div><label class="form-label">Role</label><strong>{{ selectedUser.role.toUpperCase() }}</strong></div>
            <div><label class="form-label">Status</label><span class="badge badge-dot" :class="selectedUser.is_active ? 'badge-success' : 'badge-danger'">{{ selectedUser.is_active ? 'Active' : 'Inactive' }}</span></div>
            <div><label class="form-label">Department</label><strong>{{ selectedUser.department_name || '—' }}</strong></div>
            <div><label class="form-label">Manager</label><strong>{{ selectedUser.manager_name || '—' }}</strong></div>
          </div>

          <div style="padding-top:16px;border-top:1px solid var(--border-light)">
            <button v-if="selectedUser.is_active" class="btn btn-danger" @click="toggleActive(selectedUser)" style="width:100%">🚫 Deactivate User</button>
            <button v-else class="btn btn-success" @click="toggleActive(selectedUser)" style="width:100%">✅ Reactivate User</button>
            <p style="font-size:0.75rem;color:var(--text-muted);margin-top:8px">Deactivating a user revokes their login access but keeps their historical data (like past goal sheets) intact.</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Create User Modal -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal">
        <div class="modal-header"><h3>Add New User</h3><button class="btn btn-ghost btn-sm" @click="showModal = false">✕</button></div>
        <div class="modal-body">
          <div class="form-group"><label class="form-label">Full Name</label><input v-model="newUser.full_name" class="form-input" required /></div>
          <div class="form-group"><label class="form-label">Email</label><input v-model="newUser.email" type="email" class="form-input" required /></div>
          <div class="form-group"><label class="form-label">Role</label><select v-model="newUser.role" class="form-select"><option value="employee">Employee</option><option value="manager">Manager</option><option value="admin">Admin</option></select></div>
          <div class="form-group"><label class="form-label">Password</label><input v-model="newUser.password" type="password" class="form-input" /></div>
        </div>
        <div class="modal-footer"><button class="btn btn-secondary" @click="showModal = false">Cancel</button><button class="btn btn-primary" @click="createUser">Create</button></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, inject } from 'vue'
import api from '../../services/api'

const toast = inject('toast')
const users = ref([])
const search = ref('')
const filterRole = ref('')
const showModal = ref(false)
const selectedUser = ref(null)
const newUser = ref({ full_name: '', email: '', role: 'employee', password: 'password123' })

onMounted(loadUsers)

async function loadUsers() {
  const { data } = await api.get('/admin/users')
  users.value = data.users
}

const filteredUsers = computed(() => {
  return users.value.filter(u => {
    if (filterRole.value && u.role !== filterRole.value) return false
    if (search.value && !u.full_name.toLowerCase().includes(search.value.toLowerCase()) && !u.email.toLowerCase().includes(search.value.toLowerCase())) return false
    return true
  })
})

function initials(n) { return n?.split(' ').map(w => w[0]).join('').toUpperCase() || '?' }

function openProfile(u) {
  selectedUser.value = u
}

async function toggleActive(u) {
  if (!confirm(`Are you sure you want to ${u.is_active ? 'deactivate' : 'reactivate'} ${u.full_name}?`)) return
  try {
    await api.put(`/admin/users/${u.id}`, { is_active: !u.is_active })
    toast?.success(`User ${u.is_active ? 'deactivated' : 'reactivated'}`)
    selectedUser.value = null
    loadUsers()
  } catch (e) {
    toast?.error(e.response?.data?.error || 'Action failed')
  }
}

async function createUser() {
  try {
    await api.post('/admin/users', newUser.value)
    showModal.value = false
    loadUsers()
    toast?.success('User created!')
  } catch (e) {
    toast?.error(e.response?.data?.error || 'Failed to create user')
  }
}
</script>

<style scoped>
.inactive-row {
  opacity: 0.6;
}
.inactive-row td {
  text-decoration: line-through;
}
.inactive-row td strong {
  text-decoration: none;
}
</style>
