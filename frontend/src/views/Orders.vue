<script setup>
import { onMounted, ref, reactive, computed } from 'vue'
import { useCrmStore } from '../stores/crm'
import Icon from '../components/Icon.vue'
import Modal from '../components/Modal.vue'

const crm = useCrmStore()

const statusFilter = ref('')
const customerFilter = ref('')
const detailOrder = ref(null)       // ko'rish uchun
const createModalOpen = ref(false)
const statusModalOpen = ref(false)
const editingOrder = ref(null)
const saving = ref(false)

// ── Yangi buyurtma form ────────────────────────────────────────────────
const form = reactive({
  customer_id: null,
  status: 'pending',
  notes: '',
  items: [],            // [{ product_id, quantity, unit_price }]
})

const addItemRow = () =>
  form.items.push({ product_id: null, quantity: 1, unit_price: 0 })

const removeItemRow = (i) => form.items.splice(i, 1)

function onProductChange(idx) {
  const pid = Number(form.items[idx].product_id)
  const product = crm.products.find((p) => p.id === pid)
  if (product) form.items[idx].unit_price = product.price
}

const formTotal = computed(() =>
  form.items.reduce((s, r) => s + Number(r.quantity) * Number(r.unit_price), 0)
)

// ── Status update form ─────────────────────────────────────────────────
const statusForm = reactive({ status: '', notes: '' })

// ── Constants ──────────────────────────────────────────────────────────
const STATUSES = ['pending', 'confirmed', 'shipped', 'delivered', 'cancelled']

const STATUS_META = {
  pending:   { label: 'Kutilmoqda',  badge: 'badge-amber', icon: 'zap' },
  confirmed: { label: 'Tasdiqlandi', badge: 'badge-blue',  icon: 'check' },
  shipped:   { label: 'Yuborildi',   badge: 'badge-blue',  icon: 'truck' },
  delivered: { label: 'Yetkazildi',  badge: 'badge-green', icon: 'check' },
  cancelled: { label: 'Bekor',       badge: 'badge-red',   icon: 'trash' },
}

// ── Computed ───────────────────────────────────────────────────────────
const customerMap = computed(() => {
  const m = {}
  for (const c of crm.customers) m[c.id] = c.name
  return m
})

const productMap = computed(() => {
  const m = {}
  for (const p of crm.products) m[p.id] = p
  return m
})

const summaryStats = computed(() => {
  const list = crm.orders
  return {
    total:     list.length,
    pending:   list.filter((o) => o.status === 'pending').length,
    delivered: list.filter((o) => o.status === 'delivered').length,
    revenue:   list
      .filter((o) => o.status === 'delivered')
      .reduce((s, o) => s + o.total_amount, 0),
  }
})

// ── Helpers ────────────────────────────────────────────────────────────
function money(v) {
  return '$' + Number(v || 0).toLocaleString(undefined, {
    minimumFractionDigits: 2, maximumFractionDigits: 2,
  })
}

function orderId(id) {
  return `#${String(id).padStart(5, '0')}`
}

// ── Data loading ───────────────────────────────────────────────────────
async function load() {
  const params = {}
  if (statusFilter.value)   params.status = statusFilter.value
  if (customerFilter.value) params.customer_id = customerFilter.value
  await crm.fetchOrders(params)
}

async function bootstrap() {
  await Promise.all([crm.fetchOrders(), crm.fetchCustomers(), crm.fetchProducts()])
}

// ── Create order ───────────────────────────────────────────────────────
function openCreate() {
  Object.assign(form, {
    customer_id: crm.customers[0]?.id || null,
    status: 'pending',
    notes: '',
    items: [],
  })
  addItemRow()
  createModalOpen.value = true
}

async function saveOrder() {
  if (!form.customer_id) return
  if (form.items.length === 0) return
  saving.value = true
  try {
    const payload = {
      customer_id: Number(form.customer_id),
      status: form.status,
      notes: form.notes || null,
      items: form.items
        .filter((r) => r.product_id)
        .map((r) => ({
          product_id: Number(r.product_id),
          quantity:   Number(r.quantity),
          unit_price: Number(r.unit_price),
        })),
    }
    await crm.createOrder(payload)
    createModalOpen.value = false
  } finally {
    saving.value = false
  }
}

// ── Status update ──────────────────────────────────────────────────────
function openStatusModal(order) {
  editingOrder.value = order
  statusForm.status = order.status
  statusForm.notes  = order.notes || ''
  statusModalOpen.value = true
}

async function saveStatus() {
  saving.value = true
  try {
    await crm.updateOrderStatus(
      editingOrder.value.id,
      statusForm.status,
      statusForm.notes || null,
    )
    statusModalOpen.value = false
  } finally {
    saving.value = false
  }
}

// ── Delete ─────────────────────────────────────────────────────────────
async function remove(order) {
  if (confirm(`${orderId(order.id)} buyurtmani o'chiramizmi?`))
    await crm.deleteOrder(order.id)
}

// ── Detail drawer ──────────────────────────────────────────────────────
function openDetail(order) { detailOrder.value = order }
function closeDetail()     { detailOrder.value = null }

onMounted(bootstrap)
</script>

<template>
  <div class="orders-page">
    <!-- ── Header ── -->
    <header class="page-head">
      <div>
        <h1>Buyurtmalar</h1>
        <p class="text-muted">{{ crm.orders.length }} ta buyurtma</p>
      </div>
      <button class="btn btn-primary" @click="openCreate">
        <Icon name="plus" :size="16" /> Buyurtma qo'shish
      </button>
    </header>

    <!-- ── Summary stats ── -->
    <div class="stat-row">
      <div class="stat-pill">
        <span class="stat-pill-label">Jami</span>
        <span class="stat-pill-val">{{ summaryStats.total }}</span>
      </div>
      <div class="stat-pill">
        <span class="stat-pill-label">Kutilmoqda</span>
        <span class="stat-pill-val warn">{{ summaryStats.pending }}</span>
      </div>
      <div class="stat-pill">
        <span class="stat-pill-label">Yetkazildi</span>
        <span class="stat-pill-val accent">{{ summaryStats.delivered }}</span>
      </div>
      <div class="stat-pill">
        <span class="stat-pill-label">Daromad (yetkazilgan)</span>
        <span class="stat-pill-val">{{ money(summaryStats.revenue) }}</span>
      </div>
    </div>

    <!-- ── Filters ── -->
    <div class="toolbar card">
      <select class="select filter-select" v-model="statusFilter" @change="load">
        <option value="">Barcha holatlar</option>
        <option v-for="s in STATUSES" :key="s" :value="s">{{ STATUS_META[s].label }}</option>
      </select>
      <select class="select filter-select" v-model="customerFilter" @change="load">
        <option value="">Barcha mijozlar</option>
        <option v-for="c in crm.customers" :key="c.id" :value="c.id">{{ c.name }}</option>
      </select>
    </div>

    <!-- ── Orders table ── -->
    <div class="card table-card">
      <table class="table">
        <thead>
          <tr>
            <th>№</th>
            <th>Mijoz</th>
            <th>Mahsulotlar</th>
            <th>Jami</th>
            <th>Holat</th>
            <th>Sana</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="o in crm.orders" :key="o.id" class="order-row">
            <td>
              <span class="order-id">{{ orderId(o.id) }}</span>
            </td>
            <td><strong>{{ customerMap[o.customer_id] || '—' }}</strong></td>
            <td>
              <div class="items-preview">
                <span
                  v-for="item in o.items.slice(0, 2)"
                  :key="item.id"
                  class="item-chip"
                >
                  {{ productMap[item.product_id]?.name?.split(' ').slice(0,2).join(' ') || `Mahsulot #${item.product_id}` }}
                  <em>×{{ item.quantity }}</em>
                </span>
                <span v-if="o.items.length > 2" class="item-chip more">
                  +{{ o.items.length - 2 }} ta
                </span>
              </div>
            </td>
            <td class="mono price-cell">{{ money(o.total_amount) }}</td>
            <td>
              <span class="badge" :class="STATUS_META[o.status]?.badge || 'badge-gray'">
                {{ STATUS_META[o.status]?.label || o.status }}
              </span>
            </td>
            <td class="date-cell text-muted">
              {{ new Date(o.created_at).toLocaleDateString('uz-UZ') }}
            </td>
            <td>
              <div class="row-actions">
                <button class="btn btn-ghost btn-sm" @click="openDetail(o)" title="Ko'rish">
                  <Icon name="eye" :size="15" />
                </button>
                <button class="btn btn-ghost btn-sm" @click="openStatusModal(o)" title="Holat o'zgartirish">
                  <Icon name="edit" :size="15" />
                </button>
                <button class="btn btn-ghost btn-sm" @click="remove(o)" title="O'chirish">
                  <Icon name="trash" :size="15" />
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="crm.orders.length === 0">
            <td colspan="7" class="empty">Buyurtma topilmadi.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- ── Detail drawer ── -->
    <Teleport to="body">
      <div v-if="detailOrder" class="drawer-overlay" @click.self="closeDetail">
        <div class="drawer">
          <div class="drawer-head">
            <div>
              <h2>{{ orderId(detailOrder.id) }}</h2>
              <span class="badge" :class="STATUS_META[detailOrder.status]?.badge">
                {{ STATUS_META[detailOrder.status]?.label }}
              </span>
            </div>
            <button class="btn btn-ghost btn-sm" @click="closeDetail">✕</button>
          </div>

          <div class="drawer-section">
            <div class="detail-row">
              <span class="detail-label">Mijoz</span>
              <span>{{ customerMap[detailOrder.customer_id] || '—' }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">Sana</span>
              <span>{{ new Date(detailOrder.created_at).toLocaleString('uz-UZ') }}</span>
            </div>
            <div v-if="detailOrder.notes" class="detail-row">
              <span class="detail-label">Izoh</span>
              <span>{{ detailOrder.notes }}</span>
            </div>
          </div>

          <div class="drawer-section">
            <h3 class="section-title">Mahsulotlar</h3>
            <table class="inner-table">
              <thead>
                <tr>
                  <th>Mahsulot</th>
                  <th>Narx</th>
                  <th>Dona</th>
                  <th>Jami</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in detailOrder.items" :key="item.id">
                  <td>{{ productMap[item.product_id]?.name || `#${item.product_id}` }}</td>
                  <td class="mono">{{ money(item.unit_price) }}</td>
                  <td>{{ item.quantity }}</td>
                  <td class="mono"><strong>{{ money(item.unit_price * item.quantity) }}</strong></td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="drawer-total">
            <span>Umumiy summa</span>
            <span class="total-val">{{ money(detailOrder.total_amount) }}</span>
          </div>

          <div class="drawer-footer">
            <button class="btn btn-secondary" @click="openStatusModal(detailOrder); closeDetail()">
              <Icon name="edit" :size="15" /> Holat o'zgartirish
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- ── Create order modal ── -->
    <Modal :open="createModalOpen" title="Yangi buyurtma" @close="createModalOpen = false">
      <form @submit.prevent="saveOrder">
        <div class="form-row">
          <div class="form-group">
            <label class="field-label">Mijoz *</label>
            <select class="select" v-model="form.customer_id" required>
              <option v-for="c in crm.customers" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
          </div>
          <div class="form-group">
            <label class="field-label">Holat</label>
            <select class="select" v-model="form.status">
              <option v-for="s in STATUSES" :key="s" :value="s">{{ STATUS_META[s].label }}</option>
            </select>
          </div>
        </div>

        <!-- Items -->
        <div class="form-group">
          <div class="items-header">
            <label class="field-label">Mahsulotlar *</label>
            <button type="button" class="btn btn-ghost btn-sm" @click="addItemRow">
              <Icon name="plus" :size="13" /> Qo'shish
            </button>
          </div>

          <div class="item-rows">
            <div v-for="(row, idx) in form.items" :key="idx" class="item-row">
              <select class="select item-select" v-model="row.product_id" @change="onProductChange(idx)" required>
                <option :value="null" disabled>Mahsulot tanlang</option>
                <option
                  v-for="p in crm.products.filter(p => p.status === 'active')"
                  :key="p.id"
                  :value="p.id"
                >
                  {{ p.name }} — {{ money(p.price) }}
                </option>
              </select>
              <input class="input qty-input" type="number" min="1" v-model.number="row.quantity" placeholder="Dona" />
              <input class="input price-input" type="number" min="0" step="0.01" v-model.number="row.unit_price" placeholder="Narx" />
              <button type="button" class="btn btn-ghost btn-sm del-btn" @click="removeItemRow(idx)">
                <Icon name="trash" :size="14" />
              </button>
            </div>
            <div v-if="form.items.length === 0" class="no-items-hint">
              Kamida 1 ta mahsulot qo'shing
            </div>
          </div>

          <div class="form-total">
            Jami: <strong>{{ money(formTotal) }}</strong>
          </div>
        </div>

        <div class="form-group">
          <label class="field-label">Izoh</label>
          <textarea class="textarea" rows="2" v-model="form.notes"></textarea>
        </div>

        <div class="modal-actions">
          <button type="button" class="btn btn-ghost" @click="createModalOpen = false">Bekor qilish</button>
          <button type="submit" class="btn btn-primary" :disabled="saving || form.items.length === 0">
            {{ saving ? 'Saqlanmoqda...' : 'Buyurtma yaratish' }}
          </button>
        </div>
      </form>
    </Modal>

    <!-- ── Status modal ── -->
    <Modal :open="statusModalOpen" title="Holat o'zgartirish" @close="statusModalOpen = false">
      <form @submit.prevent="saveStatus">
        <div class="form-group">
          <label class="field-label">Yangi holat</label>
          <div class="status-grid">
            <button
              v-for="s in STATUSES"
              :key="s"
              type="button"
              class="status-btn"
              :class="{ 'status-btn-active': statusForm.status === s, [`status-${s}`]: true }"
              @click="statusForm.status = s"
            >
              {{ STATUS_META[s].label }}
            </button>
          </div>
        </div>
        <div class="form-group">
          <label class="field-label">Izoh (ixtiyoriy)</label>
          <textarea class="textarea" rows="2" v-model="statusForm.notes"></textarea>
        </div>
        <div class="modal-actions">
          <button type="button" class="btn btn-ghost" @click="statusModalOpen = false">Bekor qilish</button>
          <button type="submit" class="btn btn-primary" :disabled="saving">
            {{ saving ? 'Saqlanmoqda...' : 'Saqlash' }}
          </button>
        </div>
      </form>
    </Modal>
  </div>
</template>

<style scoped>
.orders-page { container-type: inline-size; }

/* ── Header ── */
.page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-lg);
}
.page-head h1 { font-size: 24px; }

/* ── Stats ── */
.stat-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-md);
  margin-bottom: var(--space-md);
}
.stat-pill {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 14px 20px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.stat-pill-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-muted-foreground);
}
.stat-pill-val {
  font-size: 24px;
  font-weight: 700;
  font-family: var(--font-mono);
  color: var(--color-foreground);
}
.stat-pill-val.accent { color: var(--color-accent); }
.stat-pill-val.warn   { color: var(--color-warning); }

/* ── Toolbar ── */
.toolbar {
  display: flex;
  gap: var(--space-md);
  padding: var(--space-md);
  margin-bottom: var(--space-md);
}
.filter-select { width: 200px; }

/* ── Table ── */
.table-card { padding: 0; overflow: hidden; }
.order-id {
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 600;
  color: var(--color-primary);
}
.price-cell { font-weight: 600; }
.date-cell  { font-size: 13px; white-space: nowrap; }

/* Items preview */
.items-preview { display: flex; flex-wrap: wrap; gap: 4px; }
.item-chip {
  background: var(--color-muted);
  border-radius: var(--radius-sm);
  font-size: 12px;
  padding: 2px 8px;
  white-space: nowrap;
}
.item-chip em { color: var(--color-muted-foreground); font-style: normal; margin-left: 2px; }
.item-chip.more { background: #ede9fe; color: #6d28d9; }

.row-actions { display: flex; gap: 4px; justify-content: flex-end; }
.empty { text-align: center; color: var(--color-muted-foreground); padding: var(--space-xl); }

/* ── Detail drawer ── */
.drawer-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.35);
  z-index: 200;
  display: flex;
  justify-content: flex-end;
}
.drawer {
  width: 480px;
  max-width: 95vw;
  height: 100%;
  background: var(--color-surface);
  border-left: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  padding: var(--space-xl);
  overflow-y: auto;
  animation: slideIn 220ms ease;
}
@keyframes slideIn {
  from { transform: translateX(100%); opacity: 0; }
  to   { transform: translateX(0);    opacity: 1; }
}
.drawer-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--space-lg);
}
.drawer-head h2 { font-size: 20px; margin-bottom: 6px; }
.drawer-section  { margin-bottom: var(--space-lg); }
.section-title   { font-size: 13px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--color-muted-foreground); margin-bottom: var(--space-sm); }
.detail-row { display: flex; gap: var(--space-md); margin-bottom: var(--space-sm); font-size: 14px; }
.detail-label { min-width: 80px; color: var(--color-muted-foreground); }

.inner-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.inner-table th { text-align: left; padding: 8px; border-bottom: 1px solid var(--color-border); color: var(--color-muted-foreground); font-size: 11px; text-transform: uppercase; }
.inner-table td { padding: 8px; border-bottom: 1px solid var(--color-border); }

.drawer-total {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-md) 0;
  border-top: 2px solid var(--color-border);
  margin-top: auto;
}
.total-val { font-size: 20px; font-weight: 700; font-family: var(--font-mono); }
.drawer-footer { padding-top: var(--space-md); }

/* ── Create modal ── */
.form-group  { margin-bottom: var(--space-md); }
.form-row    { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-md); }
.items-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-sm); }
.item-rows   { display: flex; flex-direction: column; gap: var(--space-sm); }
.item-row    { display: grid; grid-template-columns: 1fr 80px 100px 36px; gap: 6px; align-items: center; }
.item-select { width: 100%; }
.qty-input   { text-align: center; }
.price-input { text-align: right; }
.del-btn     { padding: 6px; }
.no-items-hint { text-align: center; color: var(--color-muted-foreground); font-size: 13px; padding: var(--space-md); border: 1px dashed var(--color-border); border-radius: var(--radius-md); }
.form-total  { text-align: right; margin-top: var(--space-sm); font-size: 15px; color: var(--color-muted-foreground); }
.modal-actions { display: flex; justify-content: flex-end; gap: var(--space-sm); margin-top: var(--space-lg); }

/* ── Status grid ── */
.status-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.status-btn {
  padding: 8px 12px;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 500;
  border: 1.5px solid var(--color-border);
  background: transparent;
  color: var(--color-foreground);
  cursor: pointer;
  transition: all 150ms ease;
}
.status-btn:hover    { border-color: var(--color-primary); color: var(--color-primary); }
.status-btn-active   { border-color: var(--color-primary) !important; background: var(--color-primary) !important; color: #fff !important; }

@container (max-width: 700px) {
  .stat-row { grid-template-columns: repeat(2, 1fr); }
  .item-row { grid-template-columns: 1fr 60px 80px 32px; }
}
@media (max-width: 768px) {
  .stat-row { grid-template-columns: repeat(2, 1fr); }
  .toolbar  { flex-wrap: wrap; }
  .filter-select { width: 100%; }
}
</style>
