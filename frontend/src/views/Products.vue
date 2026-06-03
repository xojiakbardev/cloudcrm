<script setup>
import { onMounted, ref, reactive, computed } from 'vue'
import { useCrmStore } from '../stores/crm'
import Icon from '../components/Icon.vue'
import Modal from '../components/Modal.vue'

const crm = useCrmStore()
const search = ref('')
const statusFilter = ref('')
const categoryFilter = ref('')
const modalOpen = ref(false)
const editingId = ref(null)
const saving = ref(false)

const CATEGORIES = [
  'Kiyim-kechak',
  'Poyabzal',
  'Aksessuarlar',
  'Sport anjomlar',
  'Elektronika',
  'Uy-ro\'zg\'or',
  'Go\'zallik',
  'Oziq-ovqat',
  'General',
]

const STATUS_BADGE = {
  active: 'badge-green',
  draft: 'badge-amber',
  archived: 'badge-gray',
}

const STATUS_LABEL = {
  active: 'Faol',
  draft: 'Qoralama',
  archived: 'Arxivlangan',
}

const form = reactive({
  name: '',
  sku: '',
  category: 'General',
  description: '',
  price: 0,
  stock: 0,
  status: 'active',
})

const uniqueCategories = computed(() => {
  const cats = new Set(crm.products.map((p) => p.category).filter(Boolean))
  return [...cats].sort()
})

const totalValue = computed(() =>
  crm.products.reduce((s, p) => s + p.price * p.stock, 0)
)
const activeCount = computed(() =>
  crm.products.filter((p) => p.status === 'active').length
)
const lowStockCount = computed(() =>
  crm.products.filter((p) => p.stock > 0 && p.stock < 10).length
)

function money(v) {
  return '$' + Number(v || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function stockClass(stock) {
  if (stock === 0) return 'stock-zero'
  if (stock < 10) return 'stock-low'
  return 'stock-ok'
}

async function load() {
  const params = {}
  if (search.value) params.q = search.value
  if (statusFilter.value) params.status = statusFilter.value
  if (categoryFilter.value) params.category = categoryFilter.value
  await crm.fetchProducts(params)
}

function openCreate() {
  editingId.value = null
  Object.assign(form, {
    name: '', sku: '', category: 'General', description: '',
    price: 0, stock: 0, status: 'active',
  })
  modalOpen.value = true
}

function openEdit(p) {
  editingId.value = p.id
  Object.assign(form, {
    name: p.name,
    sku: p.sku,
    category: p.category || 'General',
    description: p.description || '',
    price: p.price,
    stock: p.stock,
    status: p.status,
  })
  modalOpen.value = true
}

async function save() {
  saving.value = true
  try {
    const payload = { ...form, price: Number(form.price), stock: Number(form.stock) }
    if (editingId.value) {
      await crm.updateProduct(editingId.value, payload)
    } else {
      await crm.createProduct(payload)
    }
    modalOpen.value = false
  } finally {
    saving.value = false
  }
}

async function remove(p) {
  if (confirm(`"${p.name}" mahsulotini o'chiramizmi?`)) {
    await crm.deleteProduct(p.id)
  }
}

onMounted(load)
</script>

<template>
  <div>
    <header class="page-head">
      <div>
        <h1>Mahsulotlar</h1>
        <p class="text-muted">{{ crm.products.length }} ta mahsulot</p>
      </div>
      <button class="btn btn-primary" @click="openCreate">
        <Icon name="plus" :size="16" /> Mahsulot qo'shish
      </button>
    </header>

    <!-- Stats row -->
    <div class="stat-row">
      <div class="stat-pill">
        <span class="stat-pill-label">Ombor qiymati</span>
        <span class="stat-pill-val">{{ money(totalValue) }}</span>
      </div>
      <div class="stat-pill">
        <span class="stat-pill-label">Faol mahsulotlar</span>
        <span class="stat-pill-val accent">{{ activeCount }}</span>
      </div>
      <div class="stat-pill">
        <span class="stat-pill-label">Kam qolgan (&lt;10)</span>
        <span class="stat-pill-val warn">{{ lowStockCount }}</span>
      </div>
    </div>

    <!-- Filters -->
    <div class="toolbar card">
      <div class="search-box">
        <Icon name="search" :size="16" class="search-icon" />
        <input
          class="input"
          placeholder="Nomi, SKU yoki kategoriya bo'yicha..."
          v-model="search"
          @input="load"
        />
      </div>
      <select class="select filter-select" v-model="categoryFilter" @change="load">
        <option value="">Barcha kategoriyalar</option>
        <option v-for="cat in uniqueCategories" :key="cat" :value="cat">{{ cat }}</option>
      </select>
      <select class="select filter-select" v-model="statusFilter" @change="load">
        <option value="">Barcha holatlar</option>
        <option value="active">Faol</option>
        <option value="draft">Qoralama</option>
        <option value="archived">Arxivlangan</option>
      </select>
    </div>

    <!-- Table -->
    <div class="card table-card">
      <table class="table">
        <thead>
          <tr>
            <th>Nomi</th>
            <th>SKU</th>
            <th>Kategoriya</th>
            <th>Narx</th>
            <th>Ombor</th>
            <th>Holat</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in crm.products" :key="p.id">
            <td>
              <strong>{{ p.name }}</strong>
              <div v-if="p.description" class="text-muted small desc-clip">{{ p.description }}</div>
            </td>
            <td><code class="sku-code">{{ p.sku }}</code></td>
            <td>
              <span class="cat-tag">{{ p.category }}</span>
            </td>
            <td class="mono price-cell">{{ money(p.price) }}</td>
            <td>
              <span class="stock-badge" :class="stockClass(p.stock)">
                {{ p.stock }}
              </span>
            </td>
            <td>
              <span class="badge" :class="STATUS_BADGE[p.status] || 'badge-gray'">
                {{ STATUS_LABEL[p.status] || p.status }}
              </span>
            </td>
            <td>
              <div class="row-actions">
                <button class="btn btn-ghost btn-sm" @click="openEdit(p)" aria-label="Tahrirlash">
                  <Icon name="edit" :size="15" />
                </button>
                <button class="btn btn-ghost btn-sm" @click="remove(p)" aria-label="O'chirish">
                  <Icon name="trash" :size="15" />
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="crm.products.length === 0">
            <td colspan="7" class="empty">Mahsulot topilmadi.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal -->
    <Modal
      :open="modalOpen"
      :title="editingId ? 'Mahsulotni tahrirlash' : 'Mahsulot qo\'shish'"
      @close="modalOpen = false"
    >
      <form @submit.prevent="save">
        <div class="form-group">
          <label class="field-label">Nomi *</label>
          <input class="input" v-model="form.name" required />
        </div>
        <div class="form-row">
          <div class="form-group">
            <label class="field-label">SKU *</label>
            <input class="input" v-model="form.sku" required placeholder="KIY-0001" />
          </div>
          <div class="form-group">
            <label class="field-label">Kategoriya</label>
            <select class="select" v-model="form.category">
              <option v-for="cat in CATEGORIES" :key="cat" :value="cat">{{ cat }}</option>
            </select>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label class="field-label">Narx ($)</label>
            <input class="input" type="number" min="0" step="0.01" v-model.number="form.price" />
          </div>
          <div class="form-group">
            <label class="field-label">Ombor (dona)</label>
            <input class="input" type="number" min="0" step="1" v-model.number="form.stock" />
          </div>
        </div>
        <div class="form-group">
          <label class="field-label">Holat</label>
          <select class="select" v-model="form.status">
            <option value="active">Faol</option>
            <option value="draft">Qoralama</option>
            <option value="archived">Arxivlangan</option>
          </select>
        </div>
        <div class="form-group">
          <label class="field-label">Tavsif</label>
          <textarea class="textarea" rows="3" v-model="form.description"></textarea>
        </div>
        <div class="modal-actions">
          <button type="button" class="btn btn-ghost" @click="modalOpen = false">Bekor qilish</button>
          <button type="submit" class="btn btn-primary" :disabled="saving">
            {{ saving ? 'Saqlanmoqda...' : 'Saqlash' }}
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

/* ── Stats row ── */
.stat-row {
  display: flex;
  gap: var(--space-md);
  margin-bottom: var(--space-md);
}
.stat-pill {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 12px 20px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}
.stat-pill-label {
  font-size: 12px;
  color: var(--color-muted-foreground);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.stat-pill-val {
  font-size: 22px;
  font-weight: 700;
  font-family: var(--font-mono);
  color: var(--color-foreground);
}
.stat-pill-val.accent { color: var(--color-accent); }
.stat-pill-val.warn { color: var(--color-warning); }

/* ── Toolbar ── */
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
.filter-select { width: 180px; }

/* ── Table specifics ── */
.table-card { padding: 0; overflow: hidden; }
.small { font-size: 12px; }
.desc-clip {
  font-size: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 260px;
}

.sku-code {
  font-family: var(--font-mono);
  font-size: 12px;
  background: var(--color-muted);
  padding: 2px 7px;
  border-radius: var(--radius-sm);
  color: var(--color-muted-foreground);
}

.cat-tag {
  font-size: 12px;
  background: #ede9fe;
  color: #6d28d9;
  padding: 2px 9px;
  border-radius: 999px;
  font-weight: 500;
}

.price-cell { font-weight: 600; }

.stock-badge {
  font-size: 13px;
  font-weight: 600;
  font-family: var(--font-mono);
  padding: 2px 10px;
  border-radius: var(--radius-sm);
}
.stock-ok   { background: #dcfce7; color: #047857; }
.stock-low  { background: #fef3c7; color: #b45309; }
.stock-zero { background: #fee2e2; color: #b91c1c; }

.row-actions { display: flex; gap: 4px; justify-content: flex-end; }
.empty { text-align: center; color: var(--color-muted-foreground); padding: var(--space-xl); }

/* ── Modal form ── */
.form-group { margin-bottom: var(--space-md); }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-md); }
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-sm);
  margin-top: var(--space-lg);
}

@media (max-width: 900px) {
  .stat-row { flex-wrap: wrap; }
  .toolbar { flex-wrap: wrap; }
  .filter-select { width: 100%; }
}
</style>
