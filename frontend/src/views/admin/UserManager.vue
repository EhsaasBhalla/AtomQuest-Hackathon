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
          <tr v-for="u in filteredUsers" :key="u.id">
            <td><div style="display:flex;align-items:center;gap:10px"><div class="avatar" :style="{ background: u.avatar_color }">{{ initials(u.full_name) }}</div><strong>{{ u.full_name }}</strong></div></td>
            <td style="font-size:0.8rem;color:var(--text-muted)">{{ u.email }}</td>
            <td><span class="badge" :class="u.role==='admin'?'badge-accent':u.role==='manager'?'badge-info':'badge-default'">{{ u.role }}</span></td>
            <td>{{ u.department_name || '—' }}</td>
            <td>{{ u.manager_name || '—' }}</td>
            <td><span class="badge badge-dot" :class="u.is_active ? 'badge-success' : 'badge-danger'">{{ u.is_active ? 'Active' : 'Inactive' }}</span></td>
          </tr>
        </tbody>
      </table></div>
    </div>

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
import { ref, computed, onMounted } from 'vue'
import api from '../../services/api'

const users = ref([])
const search = ref('')
const filterRole = ref('')
const showModal = ref(false)
const newUser = ref({ full_name: '', email: '', role: 'employee', password: 'password123' })

onMounted(async () => { const { data } = await api.get('/admin/users'); users.value = data.users })

const filteredUsers = computed(() => {
  return users.value.filter(u => {
    if (filterRole.value && u.role !== filterRole.value) return false
    if (search.value && !u.full_name.toLowerCase().includes(search.value.toLowerCase()) && !u.email.toLowerCase().includes(search.value.toLowerCase())) return false
    return true
  })
})

function initials(n) { return n?.split(' ').map(w => w[0]).join('').toUpperCase() || '?' }

async function createUser() {
  await api.post('/admin/users', newUser.value)
  showModal.value = false
  const { data } = await api.get('/admin/users')
  users.value = data.users
}
</script>

