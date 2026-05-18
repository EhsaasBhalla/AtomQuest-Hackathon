<template>
  <header class="navbar">
    <div class="navbar-left">
      <button class="menu-btn" @click="$emit('toggle-sidebar')">☰</button>
      <div class="search-box" :class="{ focused: searchFocused }">
        <span class="search-icon">🔍</span>
        <input
          type="text"
          v-model="searchQuery"
          placeholder="Search goals, employees..."
          class="search-input"
          @focus="searchFocused = true"
          @blur="searchFocused = false"
          @input="debouncedSearch"
        />
        <kbd v-if="!searchFocused" class="search-shortcut">⌘K</kbd>
      </div>
    </div>
    <div class="navbar-right">
      <div class="quarter-selector">
        <select v-model="selectedQuarter" class="quarter-select" @change="$emit('quarter-change', selectedQuarter)">
          <option value="q1">Q1 — Jul</option>
          <option value="q2">Q2 — Oct</option>
          <option value="q3">Q3 — Jan</option>
          <option value="q4">Q4 — Mar/Apr</option>
        </select>
      </div>
      <button class="theme-toggle" @click="toggleTheme" :title="isDark ? 'Light Mode' : 'Dark Mode'">
        {{ isDark ? '☀️' : '🌙' }}
      </button>
      <button class="notif-btn" title="Notifications" @click.stop="showNotifs = !showNotifs; showUserMenu = false">
        🔔
        <span v-if="notifCount" class="notif-badge">{{ notifCount }}</span>
      </button>

      <!-- Notifications dropdown -->
      <div v-if="showNotifs" class="notif-dropdown" @click.stop>
        <div class="notif-header">
          <strong>Notifications</strong>
          <button class="btn btn-ghost btn-sm" @click="clearNotifs">Clear all</button>
        </div>
        <div v-if="notifications.length" class="notif-list">
          <div v-for="n in notifications" :key="n.id" class="notif-item" :class="{ unread: !n.is_read, clickable: n.link }" @click="handleNotifClick(n)">
            <span class="notif-icon">{{ n.icon }}</span>
            <div>
              <p>{{ n.message }}</p>
              <small>{{ formatTime(n.created_at) }}</small>
            </div>
          </div>
        </div>
        <div v-else class="notif-empty">No notifications</div>
      </div>

      <div class="user-menu" @click.stop="showUserMenu = !showUserMenu; showNotifs = false">
        <div class="avatar" :style="{ background: auth.user?.avatar_color || '#4f46e5' }">
          {{ auth.userInitials }}
        </div>
        <div class="user-info">
          <span class="user-name">{{ auth.userName }}</span>
          <span class="user-role">{{ auth.userRole }}</span>
        </div>
        <div v-if="showUserMenu" class="dropdown-menu" @click.stop>
          <div class="dropdown-header">
            <strong>{{ auth.user?.full_name }}</strong>
            <small>{{ auth.user?.email }}</small>
          </div>
          <hr />
          <button class="dropdown-item" @click="logout">🚪 Logout</button>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '../../stores/auth'
import { useRouter } from 'vue-router'

import api from '../../services/api'

const emit = defineEmits(['toggle-sidebar', 'quarter-change', 'search'])
const auth = useAuthStore()
const router = useRouter()
const showUserMenu = ref(false)
const showNotifs = ref(false)
const searchQuery = ref('')
const searchFocused = ref(false)
const selectedQuarter = ref('q1')
const isDark = ref(false)

const notifications = ref([])
const notifCount = computed(() => notifications.value.filter(n => !n.is_read).length)

let pollInterval = null

async function fetchNotifications() {
  if (!auth.isAuthenticated) return
  try {
    const { data } = await api.get('/notifications/')
    notifications.value = data.notifications
  } catch (e) {
    console.error('Failed to fetch notifications', e)
  }
}

async function markAsRead() {
  if (notifCount.value === 0) return
  try {
    await api.post('/notifications/read')
    notifications.value.forEach(n => n.is_read = true)
  } catch (e) {
    console.error(e)
  }
}

async function clearNotifs() {
  try {
    await api.post('/notifications/clear')
    notifications.value = []
    showNotifs.value = false
  } catch (e) {
    console.error(e)
  }
}

function formatTime(isoString) {
  if (!isoString) return 'Just now'
  const date = new Date(isoString)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  const diffHrs = Math.floor(diffMins / 60)
  if (diffHrs < 24) return `${diffHrs}h ago`
  return `${Math.floor(diffHrs / 24)}d ago`
}

function handleNotifClick(n) {
  if (n.link) {
    showNotifs.value = false
    markAsRead()
    router.push(n.link)
  }
}

let debounceTimer = null
function debouncedSearch() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    emit('search', searchQuery.value)
  }, 300)
}

onMounted(() => {
  isDark.value = document.documentElement.getAttribute('data-theme') === 'dark'
  document.addEventListener('click', closeMenus)
  fetchNotifications()
  pollInterval = setInterval(fetchNotifications, 30000) // Poll every 30s
})

onUnmounted(() => {
  document.removeEventListener('click', closeMenus)
  if (pollInterval) clearInterval(pollInterval)
})

function closeMenus() {
  showUserMenu.value = false
  if (showNotifs.value) {
    showNotifs.value = false
    markAsRead()
  }
}

function toggleTheme() {
  isDark.value = !isDark.value
  const theme = isDark.value ? 'dark' : 'light'
  document.documentElement.setAttribute('data-theme', theme)
  localStorage.setItem('theme', theme)
}

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.navbar {
  position: sticky;
  top: 0;
  height: var(--navbar-height);
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  z-index: 50;
  backdrop-filter: blur(12px);
  background: rgba(255,255,255,0.85);
}

[data-theme="dark"] .navbar {
  background: rgba(30,41,59,0.9);
}

.navbar-left, .navbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.menu-btn {
  display: none;
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 6px;
  color: var(--text-secondary);
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  padding: 6px 14px;
  min-width: 280px;
  transition: var(--transition);
}

.search-box.focused {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
  min-width: 340px;
}

.search-icon { font-size: 0.85rem; }

.search-input {
  border: none;
  background: none;
  font-family: inherit;
  font-size: 0.85rem;
  color: var(--text-primary);
  outline: none;
  width: 100%;
}

.search-shortcut {
  font-size: 0.65rem;
  padding: 2px 6px;
  border-radius: 4px;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  color: var(--text-muted);
  font-family: inherit;
  flex-shrink: 0;
}

.quarter-select {
  padding: 6px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  background: var(--bg-secondary);
  font-family: inherit;
  font-size: 0.8rem;
  color: var(--text-primary);
  cursor: pointer;
}

.theme-toggle, .notif-btn {
  background: none;
  border: none;
  font-size: 1.1rem;
  cursor: pointer;
  padding: 6px;
  border-radius: var(--radius-sm);
  transition: var(--transition);
  position: relative;
}

.theme-toggle:hover, .notif-btn:hover {
  background: var(--bg-tertiary);
}

.notif-badge {
  position: absolute;
  top: 0;
  right: 0;
  background: var(--danger);
  color: white;
  font-size: 0.6rem;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
}

.notif-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 60px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  width: 340px;
  z-index: 200;
  animation: slideUp 0.2s ease;
}

.notif-header {
  padding: 14px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border-light);
}

.notif-header strong { font-size: 0.9rem; }

.notif-list { max-height: 300px; overflow-y: auto; }

.notif-item {
  display: flex;
  gap: 10px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-light);
  transition: var(--transition);
}

.notif-item:hover { background: var(--bg-tertiary); }
.notif-item.unread { background: var(--accent-bg); }
.notif-icon { font-size: 1.1rem; flex-shrink: 0; }
.notif-item p { font-size: 0.82rem; margin: 0; color: var(--text-primary); }
.notif-item small { font-size: 0.72rem; color: var(--text-muted); }
.notif-empty { padding: 24px; text-align: center; color: var(--text-muted); font-size: 0.85rem; }

.user-menu {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: var(--radius-md);
  transition: var(--transition);
  position: relative;
}

.user-menu:hover { background: var(--bg-tertiary); }

.user-info {
  display: flex;
  flex-direction: column;
}

.user-name {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-primary);
}

.user-role {
  font-size: 0.7rem;
  color: var(--text-muted);
  text-transform: capitalize;
}

.dropdown-menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  min-width: 200px;
  z-index: 200;
  animation: slideUp 0.2s ease;
}

.dropdown-header {
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.dropdown-header small {
  color: var(--text-muted);
  font-size: 0.75rem;
}

.dropdown-menu hr {
  border: none;
  border-top: 1px solid var(--border-light);
}

.dropdown-item {
  display: block;
  width: 100%;
  padding: 10px 16px;
  border: none;
  background: none;
  font-family: inherit;
  font-size: 0.85rem;
  color: var(--text-secondary);
  cursor: pointer;
  text-align: left;
  transition: var(--transition);
}

.dropdown-item:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.notif-item.clickable {
  cursor: pointer;
}
.notif-item.clickable:hover {
  background: var(--accent-bg);
}
.notif-item.clickable p::after {
  content: ' →';
  color: var(--accent);
  font-weight: 600;
}

@media (max-width: 768px) {
  .menu-btn { display: block; }
  .search-box { min-width: 160px; }
  .user-info { display: none; }
}
</style>
