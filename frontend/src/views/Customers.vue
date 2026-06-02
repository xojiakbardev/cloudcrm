<script setup>
import { onMounted, ref, reactive } from 'vue'
import { useCrmStore } from '../stores/crm'
import Icon from '../components/Icon.vue'
import Modal from '../components/Modal.vue'

const crm = useCrmStore()
const search = ref('')
const statusFilter = ref('')
const modalOpen = ref(false)
const editingId = ref(null)
const saving = ref(false)

const form = reactive({
  name: '', email: '', phone: '', company: '', status: 'lead', notes: '',
})

const STATUS_BADGE = {
  active: 'badge-green',
  lead: 'badge-blue',
  churned: 'badge-red',
}

async function load() {
  const params = {}
  if (search.value) params.q = search.value
  if (statusFilter.value) params.status = statusFilter.value
  await crm.fetchCustomers(params)
}

function openCreate() {
  editingId.value = null
  Object.assign(form, { name: '', email: '', phone: '', company: '', status: 'lead', notes: '' })
  modalOpen.value = true
}

function openEdit(c) {
  editingId.value = c.id
  Object.assign(form, {
    name: c.name, email: c.email || '', phone: c.phone || '',
    company: c.company || '', status: c.status, notes: c.notes || '',
  })
  modalOpen.value = true
}

async function save() {
  saving.value = true
  try {
    if (editingId.value) {
      await crm.updateCustomer(editingId.value, { ...form })
    } else {
      await crm.createCustomer({ ...form })
    }
    modalOpen.value = false
  } finally {
    saving.value = false
  }
}

async function remove(c) {
  if (confirm(`"${c.name}" mijozini o'chiramizmi?`)) {
    await crm.deleteCustomer(c.id)
  }
}

const STATUS_LABEL = {
  active: 'Faol',
  lead: 'Yo\'naltirilgan',
  churned: 'Ketgan',
}

onMounted(load)
</script>

<template>
  <div>
    <header class="page-head">
      <div>
        <h1>Mijozlar</h1>
        <p class="text-muted">{{ crm.customers.length }} ta yozuv</p>
      </div>
      <button class="btn btn-primary" @click="openCreate">
        <Icon name="plus" :size="16" /> Mijoz qo'shish
      </button>
    </header>

    <div class="toolbar card">
      <div class="search-box">
        <Icon name="search" :size="16" class="search-icon" />
        <input class="input" placeholder="Ism yoki kompaniya bo'yicha qidirish..." v-model="search" @input="load" />
      </div>
      <select class="select status-select" v-model="statusFilter" @change="load">
        <option value="">Barcha holatlar</option>
        <option value="lead">Yo'naltirilgan</option>
        <option value="active">Faol</option>
        <option value="churned">Ketgan</option>
      </select>
    </div>

    <div class="card table-card">
      <table class="table">
        <thead>
          <tr>
            <th>Ism</th>
            <th>Kompaniya</th>
            <th>Aloqa</th>
            <th>Holat</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in crm.customers" :key="c.id">
            <td><strong>{{ c.name }}</strong></td>
            <td>{{ c.company || '—' }}</td>
            <td>
              <div>{{ c.email || '—' }}</div>
              <div class="text-muted mono small">{{ c.phone || '' }}</div>
            </td>
            <td><span class="badge" :class="STATUS_BADGE[c.status] || 'badge-gray'">{{ STATUS_LABEL[c.status] || c.status }}</span></td>
            <td>
              <div class="row-actions">
                <button class="btn btn-ghost btn-sm" @click="openEdit(c)" aria-label="Tahrirlash"><Icon name="edit" :size="15" /></button>
                <button class="btn btn-ghost btn-sm" @click="remove(c)" aria-label="O'chirish"><Icon name="trash" :size="15" /></button>
              </div>
            </td>
          </tr>
          <tr v-if="crm.customers.length === 0">
            <td colspan="5" class="empty">Mijoz topilmadi.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <Modal :open="modalOpen" :title="editingId ? 'Mijozni tahrirlash' : 'Mijoz qo\'shish'" @close="modalOpen = false">
      <form @submit.prevent="save">
        <div class="form-group">
          <label class="field-label">Ism *</label>
          <input class="input" v-model="form.name" required />
        </div>
        <div class="form-row">
          <div class="form-group">
            <label class="field-label">Email</label>
            <input class="input" type="email" v-model="form.email" />
          </div>
          <div class="form-group">
            <label class="field-label">Telefon</label>
            <input class="input" v-model="form.phone" />
          </div>
        </div>
        <div class="form-group">
          <label class="field-label">Kompaniya</label>
          <input class="input" v-model="form.company" />
        </div>
        <div class="form-group">
          <label class="field-label">Holat</label>
          <select class="select" v-model="form.status">
            <option value="lead">Yo'naltirilgan</option>
            <option value="active">Faol</option>
            <option value="churned">Ketgan</option>
          </select>
        </div>
        <div class="form-group">
          <label class="field-label">Izohlar</label>
          <textarea class="textarea" rows="3" v-model="form.notes"></textarea>
        </div>
        <div class="modal-actions">
          <button type="button" class="btn btn-ghost" @click="modalOpen = false">Bekor qilish</button>
          <button type="submit" class="btn btn-primary" :disabled="saving">
            {{ saving ? "Saqlanmoqda..." : 'Saqlash' }}
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
.toolbar {
  display: flex;
  gap: var(--space-md);
  margin-bottom: var(--space-md);
  padding: var(--space-md);
}
.search-box { position: relative; flex: 1; }
.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-muted-foreground);
}
.search-box .input { padding-left: 36px; }
.status-select { width: 180px; }
.table-card { padding: 0; overflow: hidden; }
.row-actions { display: flex; gap: 4px; justify-content: flex-end; }
.small { font-size: 12px; }
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
