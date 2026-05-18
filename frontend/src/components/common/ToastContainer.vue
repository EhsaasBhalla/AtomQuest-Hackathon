<template>
  <Teleport to="body">
    <div class="toast-container">
      <TransitionGroup name="toast-anim">
        <div v-for="t in toasts" :key="t.id" class="toast" :class="t.type" @click="remove(t.id)">
          <span class="toast-icon">{{ icons[t.type] }}</span>
          <div class="toast-body">
            <strong v-if="t.title">{{ t.title }}</strong>
            <p>{{ t.message }}</p>
          </div>
          <button class="toast-close" @click.stop="remove(t.id)">✕</button>
          <div class="toast-progress" :style="{ animationDuration: t.duration + 'ms' }"></div>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup>
import { ref } from 'vue'

const toasts = ref([])
const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' }
let nextId = 0

function add(message, type = 'info', title = '', duration = 4000) {
  const id = nextId++
  toasts.value.push({ id, message, type, title, duration })
  setTimeout(() => remove(id), duration)
}

function remove(id) {
  toasts.value = toasts.value.filter(t => t.id !== id)
}

defineExpose({ add })
</script>

<style scoped>
.toast-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 8px;
  pointer-events: none;
}

.toast {
  pointer-events: all;
  background: var(--bg-card, #fff);
  border: 1px solid var(--border, #e2e8f0);
  border-radius: 10px;
  padding: 14px 16px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.12);
  display: flex;
  align-items: flex-start;
  gap: 10px;
  min-width: 320px;
  max-width: 420px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
}

.toast.success { border-left: 4px solid #10b981; }
.toast.error { border-left: 4px solid #ef4444; }
.toast.warning { border-left: 4px solid #f59e0b; }
.toast.info { border-left: 4px solid #3b82f6; }

.toast-icon { font-size: 1.1rem; flex-shrink: 0; margin-top: 1px; }
.toast-body { flex: 1; }
.toast-body strong { font-size: 0.85rem; display: block; margin-bottom: 2px; color: var(--text-primary, #0f172a); }
.toast-body p { margin: 0; font-size: 0.82rem; color: var(--text-secondary, #475569); line-height: 1.4; }
.toast-close {
  background: none; border: none; color: var(--text-muted, #94a3b8);
  cursor: pointer; font-size: 0.75rem; padding: 2px; flex-shrink: 0;
}

.toast-progress {
  position: absolute; bottom: 0; left: 0; right: 0; height: 3px;
  background: currentColor; opacity: 0.2;
  animation: toast-shrink linear forwards;
}

@keyframes toast-shrink {
  from { transform: scaleX(1); transform-origin: left; }
  to { transform: scaleX(0); transform-origin: left; }
}

.toast-anim-enter-active { animation: slideInRight 0.3s ease; }
.toast-anim-leave-active { animation: slideOutRight 0.3s ease; }

@keyframes slideInRight {
  from { transform: translateX(120%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}
@keyframes slideOutRight {
  from { transform: translateX(0); opacity: 1; }
  to { transform: translateX(120%); opacity: 0; }
}
</style>
