<template>
  <div>
    <div class="page-header"><h1>{{ isEdit ? 'Edit Goal' : 'Add New Goal' }}</h1><p>{{ isEdit ? 'Update your goal details' : 'Define a new goal for your sheet' }}</p></div>
    <div class="card" style="max-width:700px">
      <form @submit.prevent="saveGoal">
        <div class="steps">
          <div class="step" :class="{ active: step >= 1, done: step > 1 }"><span>1</span> Basic Info</div>
          <div class="step-line" :class="{ done: step > 1 }"></div>
          <div class="step" :class="{ active: step >= 2, done: step > 2 }"><span>2</span> Measurement</div>
          <div class="step-line" :class="{ done: step > 2 }"></div>
          <div class="step" :class="{ active: step >= 3 }"><span>3</span> Review</div>
        </div>
        <div v-if="step === 1">
          <div class="form-group"><label class="form-label">Thrust Area *</label><select v-model="form.thrust_area" class="form-select" required><option value="">Select thrust area</option><option v-for="t in thrustAreas" :key="t" :value="t">{{ t }}</option></select></div>
          <div class="form-group"><label class="form-label">Goal Title *</label><input v-model="form.title" class="form-input" placeholder="e.g., Increase quarterly sales by 20%" required /></div>
          <div class="form-group"><label class="form-label">Description</label><textarea v-model="form.description" class="form-textarea" rows="3" placeholder="Describe the goal..."></textarea></div>
          <button type="button" class="btn btn-primary" @click="step = 2" :disabled="!form.thrust_area || !form.title">Next →</button>
        </div>
        <div v-if="step === 2">
          <div class="form-group"><label class="form-label">Unit of Measurement *</label>
            <div class="uom-grid"><label v-for="u in uomOptions" :key="u.value" class="uom-option" :class="{ selected: form.uom_type === u.value }"><input type="radio" v-model="form.uom_type" :value="u.value" style="display:none" /><span class="uom-icon">{{ u.icon }}</span><strong>{{ u.label }}</strong><small>{{ u.desc }}</small></label></div>
          </div>
          <div class="form-group" v-if="needsTarget"><label class="form-label">Target Value *</label><input v-model.number="form.target_value" type="number" class="form-input" placeholder="e.g., 100" required /></div>
          <div class="form-group" v-if="form.uom_type === 'timeline'"><label class="form-label">Target Date *</label><input v-model="form.target_date" type="date" class="form-input" required /></div>
          <div class="form-group">
            <label class="form-label">Weightage (%) * — Min: 10%, Remaining: {{ gs.remainingWeightage + (isEdit ? editOrigWeight : 0) }}%</label>
            <input v-model.number="form.weightage" type="number" class="form-input" min="10" max="100" required />
            <p v-if="form.weightage < 10" class="form-error">Minimum weightage is 10%</p>
          </div>
          <div style="display:flex;gap:8px"><button type="button" class="btn btn-secondary" @click="step = 1">← Back</button><button type="button" class="btn btn-primary" @click="step = 3" :disabled="!isStep2Valid">Next →</button></div>
        </div>
        <div v-if="step === 3">
          <div class="review-card">
            <div class="review-row"><label>Thrust Area</label><span>{{ form.thrust_area }}</span></div>
            <div class="review-row"><label>Title</label><span>{{ form.title }}</span></div>
            <div class="review-row"><label>Description</label><span>{{ form.description || '—' }}</span></div>
            <div class="review-row"><label>UoM</label><span>{{ uomLabel(form.uom_type) }}</span></div>
            <div class="review-row"><label>Target</label><span>{{ form.target_value || form.target_date || '0 incidents' }}</span></div>
            <div class="review-row"><label>Weightage</label><span><strong>{{ form.weightage }}%</strong></span></div>
          </div>
          <div style="display:flex;gap:8px;margin-top:20px">
            <button type="button" class="btn btn-secondary" @click="step = 2">← Back</button>
            <button type="submit" class="btn btn-success" :disabled="saving">{{ saving ? 'Saving...' : (isEdit ? '💾 Update Goal' : '✅ Create Goal') }}</button>
          </div>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, inject } from 'vue'
import { useGoalStore } from '../../stores/goals'
import { useRouter, useRoute } from 'vue-router'

const gs = useGoalStore()
const router = useRouter()
const route = useRoute()
const toast = inject('toast')
const step = ref(1)
const saving = ref(false)
const editOrigWeight = ref(0)
const isEdit = computed(() => !!route.params.id)
const form = ref({ thrust_area:'', title:'', description:'', uom_type:'numeric_min', target_value:null, target_date:'', weightage:10 })
const thrustAreas = ['Revenue Growth','Customer Satisfaction','Product Quality','Innovation','Operational Excellence','People Development']
const uomOptions = [
  { value:'numeric_min', label:'Numeric (Higher)', icon:'📊', desc:'Higher is better' },
  { value:'numeric_max', label:'Numeric (Lower)', icon:'📉', desc:'Lower is better' },
  { value:'percent_min', label:'% (Higher)', icon:'🔼', desc:'Higher % is better' },
  { value:'percent_max', label:'% (Lower)', icon:'🔽', desc:'Lower % is better' },
  { value:'timeline', label:'Timeline', icon:'📅', desc:'Date-based' },
  { value:'zero', label:'Zero-based', icon:'🎯', desc:'0 = Success' },
]
const needsTarget = computed(() => ['numeric_min','numeric_max','percent_min','percent_max'].includes(form.value.uom_type))
const isStep2Valid = computed(() => {
  if (form.value.weightage < 10) return false
  if (needsTarget.value && !form.value.target_value) return false
  if (form.value.uom_type === 'timeline' && !form.value.target_date) return false
  return true
})
function uomLabel(t) { return uomOptions.find(u => u.value === t)?.label || t }

onMounted(async () => {
  await gs.fetchSheet()
  if (!gs.currentSheet) await gs.createSheet()
  if (isEdit.value) {
    const goal = gs.goals.find(g => g.id === parseInt(route.params.id))
    if (goal) { form.value = { ...goal }; editOrigWeight.value = goal.weightage }
  }
})

async function saveGoal() {
  saving.value = true
  try {
    if (isEdit.value) { await gs.updateGoal(route.params.id, form.value) }
    else { await gs.addGoal(gs.currentSheet.id, form.value) }
    toast?.success(isEdit.value ? 'Goal updated!' : 'Goal created!')
    router.push('/goals')
  } catch(e) { toast?.error(e.response?.data?.error || 'Failed to save goal') }
  finally { saving.value = false }
}
</script>

<style scoped>
.steps { display:flex; align-items:center; margin-bottom:32px; }
.step { display:flex; align-items:center; gap:8px; font-size:0.85rem; color:var(--text-muted); font-weight:500; }
.step span { width:28px; height:28px; border-radius:50%; background:var(--bg-tertiary); display:flex; align-items:center; justify-content:center; font-weight:600; font-size:0.8rem; }
.step.active { color:var(--accent); } .step.active span { background:var(--accent); color:white; } .step.done span { background:var(--success); color:white; }
.step-line { flex:1; height:2px; background:var(--border); margin:0 12px; } .step-line.done { background:var(--success); }
.uom-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; }
.uom-option { padding:12px; border:2px solid var(--border); border-radius:var(--radius-md); cursor:pointer; text-align:center; transition:var(--transition); }
.uom-option:hover { border-color:var(--accent-light); } .uom-option.selected { border-color:var(--accent); background:var(--accent-bg); }
.uom-icon { font-size:1.3rem; display:block; margin-bottom:4px; } .uom-option strong { font-size:0.8rem; display:block; } .uom-option small { font-size:0.7rem; color:var(--text-muted); }
.review-card { background:var(--bg-tertiary); border-radius:var(--radius-md); padding:20px; }
.review-row { display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid var(--border-light); }
.review-row:last-child { border:none; } .review-row label { color:var(--text-muted); font-size:0.85rem; } .review-row span { font-size:0.85rem; text-align:right; max-width:60%; }
</style>
