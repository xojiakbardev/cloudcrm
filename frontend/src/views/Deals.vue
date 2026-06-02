<script setup>
import { onMounted, ref, reactive, computed } from 'vue'
import { useCrmStore } from '../stores/crm'
import Icon from '../components/Icon.vue'
import Modal from '../components/Modal.vue'

const crm = useCrmStore()
const modalOpen = ref(false)
const editingId = ref(null)
const saving = ref(false)

const STAGES = ['new', 'qualified', 'proposal', 'won', 'lost']
const STAGE_BADGE = {
  new: 'badge-gray',
  qualified: 'badge-blue',
  proposal: 'badge-amber',
  won: 'badge-green',
  lost: 'badge-red',
}

const form = reactive({ title: '', amount: 0, stage: 'new', customer_id: null })

const customerName = computed(() => {
  const map = {}
  for (const c of crm.customers) map[c.id] = c.name
  return map
})

function money(v) {
  return '$' + Number(v || 0).toLocaleString()
}

async function load() {
  await Promise.all([crm.fetchDeals(), crm.fetchCustomers()])
}

function openCreate() {
  editingId.value = null
  Object.assign(form, {
    title: '', amount: 0, stage: 'new',
    customer_id: crm.customers[0]?.id || null,
  })
  modalOpen.value = true
}

function openEdit(d) {
  editingId.value = d.id
  Object.assign(form, {
    title: d.title, amount: d.amount, stage: d.stage, customer_id: d.customer_id,
  })
  modalOpen.value = true
}

async function save() {
  saving.value = true
  try {
    const payload = { ...form, amount: Number(form.amount), customer_id: Number(form.customer_id) }
    if (editingId.value) {
      await crm.updateDeal(editingId.value, payload)
    } else {
      await crm.createDeal(payload)
    }
    modalOpen.value = false
  } finally {
    saving.value = false
  }
}

async function remove(d) {
  if (confirm(`Delete deal "${d.title}"?`)) {
    await crm.deleteDeal(d.id)
  }
}

onMounted(load)
</script>

<template>
  <div>
    <header class="page-head">
      <div>
        <h1>Deals</h1>
        <p class="text-muted">{{ crm.deals.length }} opportunities</p>
      </div>
      <button class="btn btn-primary" @click="openCreate">
        <Icon name="plus" :size="16" /> Add Deal
      </button>
    </header>

    <div class="card table-card">
      <table class="table">
        <thead>
          <tr>
            <th>Deal</th>
            <th>Customer</th>
            <th>Amount</th>
            <th>Stage</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="d in crm.deals" :key="d.id">
            <td><strong>{{ d.title }}</strong></td>
            <td>{{ customerName[d.customer_id] || '—' }}</td>
            <td class="mono">{{ money(d.amount) }}</td>
            <td><span class="badge" :class="STAGE_BADGE[d.stage]">{{ d.stage }}</span></td>
            <td>
              <div class="row-actions">
                <button class="btn btn-ghost btn-sm" @click="openEdit(d)" aria-label="Edit"><Icon name="edit" :size="15" /></button>
                <button class="btn btn-ghost btn-sm" @click="remove(d)" aria-label="Delete"><Icon name="trash" :size="15" /></button>
              </div>
            </td>
          </tr>
          <tr v-if="crm.deals.length === 0">
            <td colspan="5" class="empty">No deals yet.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <Modal :open="modalOpen" :title="editingId ? 'Edit Deal' : 'Add Deal'" @close="modalOpen = false">
      <form @submit.prevent="save">
        <div class="form-group">
          <label class="field-label">Title *</label>
          <input class="input" v-model="form.title" required />
        </div>
        <div class="form-row">
          <div class="form-group">
            <label class="field-label">Amount ($)</label>
            <input class="input" type="number" min="0" step="100" v-model.number="form.amount" />
          </div>
          <div class="form-group">
            <label class="field-label">Stage</label>
            <select class="select" v-model="form.stage">
              <option v-for="s in STAGES" :key="s" :value="s">{{ s }}</option>
            </select>
          </div>
        </div>
        <div class="form-group">
          <label class="field-label">Customer *</label>
          <select class="select" v-model="form.customer_id" required>
            <option v-for="c in crm.customers" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
        </div>
        <div class="modal-actions">
          <button type="button" class="btn btn-ghost" @click="modalOpen = false">Cancel</button>
          <button type="submit" class="btn btn-primary" :disabled="saving">
            {{ saving ? 'Saving...' : 'Save' }}
          </button>
        </div>
      </form>
    </Modal>
  </div>
</template>

<style scoped>
.page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-lg);
}
.page-head h1 { font-size: 24px; }
.table-card { padding: 0; overflow: hidden; }
.row-actions { display: flex; gap: 4px; justify-content: flex-end; }
.empty { text-align: center; color: var(--color-muted-foreground); padding: var(--space-xl); }
.form-group { margin-bottom: var(--space-md); }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-md); }
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-sm);
  margin-top: var(--space-lg);
}
</style>
