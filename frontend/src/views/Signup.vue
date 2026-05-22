<template>
  <div class="login-page">
    <div class="login-bg">
      <div class="bg-shape shape-1"></div>
      <div class="bg-shape shape-2"></div>
      <div class="bg-shape shape-3"></div>
    </div>
    <div class="login-card" style="width:500px">
      <div class="login-header">
        <div class="login-logo">⚡</div>
        <h1>Join GoalTracker</h1>
        <p>Create your employee account</p>
      </div>
      <form @submit.prevent="handleSignup" class="login-form">
        <div class="form-group">
          <label class="form-label">Full Name</label>
          <input v-model="form.full_name" type="text" class="form-input" placeholder="e.g. John Doe" required />
        </div>
        <div class="form-group">
          <label class="form-label">Email</label>
          <input v-model="form.email" type="email" class="form-input" placeholder="e.g. john@company.com" required />
        </div>
        
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
          <div class="form-group">
            <label class="form-label">Password</label>
            <input v-model="form.password" type="password" class="form-input" placeholder="Password" required minlength="6" />
          </div>
          <div class="form-group">
            <label class="form-label">Confirm Password</label>
            <input v-model="form.confirm" type="password" class="form-input" placeholder="Confirm Password" required minlength="6" />
          </div>
        </div>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
          <div class="form-group">
            <label class="form-label">Department</label>
            <select v-model="form.department_id" class="form-input" required>
              <option value="" disabled>Select Department</option>
              <option v-for="d in departments" :key="d.id" :value="d.id">{{ d.name }}</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Manager</label>
            <select v-model="form.manager_id" class="form-input" required :disabled="!form.department_id">
              <option value="" disabled>{{ form.department_id ? 'Select Manager' : 'Select a department first' }}</option>
              <option v-for="m in filteredManagers" :key="m.id" :value="m.id">{{ m.full_name }}</option>
            </select>
          </div>
        </div>

        <p v-if="errorMsg" class="form-error" style="text-align:center;margin-bottom:12px;color:#ef4444">{{ errorMsg }}</p>
        <div style="display:flex;justify-content:center;margin-top:24px">
          <button type="submit" class="btn btn-primary btn-lg" style="min-width:220px" :disabled="loading">
            {{ loading ? 'Creating Account...' : 'Sign Up' }}
          </button>
        </div>
        
        <div class="signup-link">
          Already have an account? <router-link to="/login">Sign In</router-link>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../services/api'

const router = useRouter()
const errorMsg = ref('')
const loading = ref(false)

const departments = ref([])
const managers = ref([])

const form = ref({
  full_name: '',
  email: '',
  password: '',
  confirm: '',
  department_id: '',
  manager_id: ''
})

// Filter managers by the selected department
const filteredManagers = computed(() => {
  if (!form.value.department_id) return []
  return managers.value.filter(m => m.department_id === form.value.department_id)
})

// Reset manager selection when department changes
watch(() => form.value.department_id, () => {
  form.value.manager_id = ''
})

onMounted(async () => {
  try {
    // Note: This endpoint must not require JWT
    const { data } = await api.get('/auth/register-metadata')
    departments.value = data.departments
    managers.value = data.managers
  } catch (e) {
    errorMsg.value = 'Failed to load signup configuration'
  }
})

async function handleSignup() {
  if (form.value.password !== form.value.confirm) {
    errorMsg.value = "Passwords do not match"
    return
  }
  
  loading.value = true
  errorMsg.value = ''
  try {
    await api.post('/auth/register', form.value)
    // Send to login with email pre-filled? Or just simple redirect.
    router.push({ path: '/login', query: { registered: 'true' } })
  } catch (e) {
    errorMsg.value = e.response?.data?.error || 'Registration failed'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #0f172a;
  position: relative;
  overflow: hidden;
}

.login-bg {
  position: absolute;
  inset: 0;
}

.bg-shape {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.3;
}

.shape-1 { width: 500px; height: 500px; background: #4f46e5; top: -100px; right: -100px; animation: float 8s ease-in-out infinite; }
.shape-2 { width: 400px; height: 400px; background: #7c3aed; bottom: -100px; left: -100px; animation: float 10s ease-in-out infinite reverse; }
.shape-3 { width: 300px; height: 300px; background: #3b82f6; top: 50%; left: 50%; animation: float 12s ease-in-out infinite; }

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -30px) scale(1.05); }
  66% { transform: translate(-20px, 20px) scale(0.95); }
}

.login-card {
  position: relative;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 40px;
  max-width: 95%;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.3);
  z-index: 10;
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-logo {
  width: 56px;
  height: 56px;
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  margin: 0 auto 16px;
  box-shadow: 0 8px 24px rgba(79, 70, 229, 0.4);
}

.login-header h1 {
  color: #f1f5f9;
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.login-header p {
  color: #94a3b8;
  font-size: 0.9rem;
  margin-top: 4px;
}

.login-form .form-label { color: #94a3b8; font-size: 0.85rem; }
.login-form .form-input {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.1);
  color: #f1f5f9;
  padding: 10px;
}
.login-form .form-input::placeholder { color: #64748b; }
.login-form .form-input:focus {
  border-color: #4f46e5;
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.2);
}

.login-form select.form-input option {
  background: #1e293b;
  color: #f1f5f9;
}

.signup-link {
  text-align: center;
  margin-top: 24px;
  font-size: 0.85rem;
  color: #94a3b8;
}
.signup-link a {
  color: #4f46e5;
  text-decoration: none;
  font-weight: 600;
  transition: color 0.2s;
}
.signup-link a:hover {
  color: #818cf8;
}

@media (max-width: 480px) {
  .login-card { padding: 24px; width: 90%; }
}
</style>
