<template>
  <div class="login-page">
    <div class="login-bg">
      <div class="bg-shape shape-1"></div>
      <div class="bg-shape shape-2"></div>
      <div class="bg-shape shape-3"></div>
    </div>
    <div class="login-card">
      <div class="login-header">
        <div class="login-logo">⚡</div>
        <h1>GoalTracker Pro</h1>
        <p>Performance Management Portal</p>
      </div>
      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label class="form-label">Email</label>
          <input v-model="email" type="email" class="form-input" placeholder="Enter your email"
            :class="{ error: errorMsg }" required />
        </div>
        <div class="form-group">
          <div style="display:flex; justify-content:space-between; align-items:center">
            <label class="form-label">Password</label>
            <a href="#" class="forgot-link">Forgot password?</a>
          </div>
          <input v-model="password" type="password" class="form-input" placeholder="Enter password"
            :class="{ error: errorMsg }" required />
        </div>
        <p v-if="$route.query.registered" class="form-success" style="text-align:center;margin-bottom:12px;color:#10b981;font-size:0.85rem">Registration successful! You can now sign in.</p>
        <p v-if="errorMsg" class="form-error" style="text-align:center;margin-bottom:12px;color:#ef4444;font-size:0.85rem">{{ errorMsg }}</p>
        <div style="display:flex;justify-content:center;margin-top:24px">
          <button type="submit" class="btn btn-primary btn-lg" style="min-width:220px" :disabled="loading">
            {{ loading ? 'Signing in...' : 'Sign In' }}
          </button>
        </div>
      </form>
      <div class="demo-creds">
        <p class="demo-title">Demo Credentials</p>
        <div class="cred-grid">
          <button v-for="c in creds" :key="c.role" class="cred-btn" @click="quickLogin(c)">
            <span class="cred-role">{{ c.role }}</span>
            <span class="cred-email">{{ c.email }}</span>
          </button>
        </div>
      </div>
      <div class="signup-link">
        Don't have an account? <router-link to="/signup">Sign Up</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()
const email = ref('')
const password = ref('')
const errorMsg = ref('')
const loading = ref(false)

const creds = [
  { role: 'Admin', email: 'admin@company.com', pass: 'admin123' },
  { role: 'Manager', email: 'manager@company.com', pass: 'manager123' },
  { role: 'Employee', email: 'employee@company.com', pass: 'emp123' },
]

async function handleLogin() {
  loading.value = true
  errorMsg.value = ''
  try {
    await auth.login(email.value, password.value)
    router.push('/dashboard')
  } catch (e) {
    errorMsg.value = e.response?.data?.error || 'Login failed'
  } finally {
    loading.value = false
  }
}

function quickLogin(c) {
  email.value = c.email
  password.value = c.pass
  handleLogin()
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

.shape-1 {
  width: 500px;
  height: 500px;
  background: #4f46e5;
  top: -100px;
  right: -100px;
  animation: float 8s ease-in-out infinite;
}

.shape-2 {
  width: 400px;
  height: 400px;
  background: #7c3aed;
  bottom: -100px;
  left: -100px;
  animation: float 10s ease-in-out infinite reverse;
}

.shape-3 {
  width: 300px;
  height: 300px;
  background: #3b82f6;
  top: 50%;
  left: 50%;
  animation: float 12s ease-in-out infinite;
}

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
  width: 420px;
  max-width: 95%;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.3);
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

.login-form .form-label {
  color: #94a3b8;
}

.login-form .form-input {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.1);
  color: #f1f5f9;
}

.login-form .form-input::placeholder {
  color: #64748b;
}

.login-form .form-input:focus {
  border-color: #4f46e5;
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.2);
}

.demo-creds {
  margin-top: 28px;
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.demo-title {
  font-size: 0.75rem;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  text-align: center;
  margin-bottom: 12px;
}

.cred-grid {
  display: flex;
  gap: 8px;
}

.cred-btn {
  flex: 1;
  padding: 10px 8px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.cred-btn:hover {
  background: rgba(79, 70, 229, 0.2);
  border-color: rgba(79, 70, 229, 0.4);
  transform: translateY(-2px);
}

.cred-role {
  font-size: 0.8rem;
  font-weight: 600;
  color: #f1f5f9;
}

.cred-email {
  font-size: 0.65rem;
  color: #64748b;
  word-break: break-all;
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

.forgot-link {
  font-size: 0.75rem;
  color: #4f46e5;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s;
}
.forgot-link:hover {
  color: #818cf8;
}

@media (max-width: 480px) {
  .login-card {
    padding: 24px;
    width: 90%;
  }
  .cred-grid {
    flex-direction: column;
  }
  .cred-btn {
    flex-direction: row;
    justify-content: space-between;
    padding: 12px 16px;
  }
}
</style>
