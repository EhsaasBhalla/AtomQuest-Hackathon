<template>
  <div id="app-root">
    <div v-if="isAuthenticated" class="app-layout">
      <Sidebar :collapsed="sidebarCollapsed" @toggle="sidebarCollapsed = !sidebarCollapsed" />
      <div class="main-content" :class="{ collapsed: sidebarCollapsed }">
        <Navbar
          @toggle-sidebar="sidebarCollapsed = !sidebarCollapsed"
          @quarter-change="currentQuarter = $event"
          @search="handleSearch"
        />
        <div class="page-content">
          <router-view v-slot="{ Component }">
            <transition name="fade" mode="out-in">
              <component :is="Component" :key="$route.fullPath" />
            </transition>
          </router-view>
        </div>
      </div>
    </div>
    <router-view v-else />
    <ToastContainer ref="toastRef" />
  </div>
</template>

<script setup>
import { ref, computed, provide, onMounted, watch } from 'vue'
import { useAuthStore } from './stores/auth'
import Sidebar from './components/common/Sidebar.vue'
import Navbar from './components/common/Navbar.vue'
import ToastContainer from './components/common/ToastContainer.vue'

const auth = useAuthStore()
const isAuthenticated = computed(() => auth.isAuthenticated)
const sidebarCollapsed = ref(false)
const currentQuarter = ref('q1')
const toastRef = ref(null)

// Provide toast globally
provide('toast', {
  success: (msg, title) => toastRef.value?.add(msg, 'success', title),
  error: (msg, title) => toastRef.value?.add(msg, 'error', title),
  warning: (msg, title) => toastRef.value?.add(msg, 'warning', title),
  info: (msg, title) => toastRef.value?.add(msg, 'info', title),
})

// Provide quarter globally
provide('currentQuarter', currentQuarter)

// Dark mode - sync to documentElement
onMounted(() => {
  const saved = localStorage.getItem('theme') || 'light'
  document.documentElement.setAttribute('data-theme', saved)
})

function handleSearch(query) {
  // Global search handled at app level
  console.log('Search:', query)
}
</script>
