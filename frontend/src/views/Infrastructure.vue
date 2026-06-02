<script setup>
import { onMounted, onBeforeUnmount, ref, computed } from 'vue'
import { useInfraStore } from '../stores/infra'
import { useControlStore } from '../stores/control'
import NetworkTopology from '../components/NetworkTopology.vue'
import LayerDiagram from '../components/LayerDiagram.vue'
import Icon from '../components/Icon.vue'

const infra = useInfraStore()
const control = useControlStore()

const REFRESH_MS = 2000
const loadTesting = ref(false)
const concurrency = ref(20)
const firstLoad = ref(true)
const drainingId = ref('')
const removingId = ref('')
let refreshTimer = null
let loadTimer = null

const healthyCount = computed(() => infra.instances.filter((i) => i.status === 'healthy').length)
const totalRequests = computed(() => infra.instances.reduce((s, i) => s + i.request_count, 0))

const quickTargets = computed(() => {
  const out = []
  for (let n = control.limits.min; n <= control.limits.max; n++) out.push(n)
  return out
})

const distribution = computed(() => {
  const counts = {}
  for (const p of infra.pingLog) {
    counts[p.served_by] = (counts[p.served_by] || 0) + 1
  }
  const total = infra.pingLog.length || 1
  return Object.entries(counts)
    .map(([id, count]) => ({ id, count, pct: Math.round((count / total) * 100) }))
    .sort((a, b) => b.count - a.count)
})

async function refresh() {
  // Pause the polling while a scale or remove action is in flight — otherwise
  // the auto-refresh races with the user's action and the UI flickers.
  if (control.busy || drainingId.value || removingId.value) return
  try {
    await Promise.all([
      infra.fetchInstances(),
      infra.fetchTopology(),
      control.fetchStatus(),
    ])
  } catch (e) {
    // Transient network error — next tick will retry, don't clobber UI.
  }
}

async function sendBurst() {
  const reqs = []
  for (let i = 0; i < concurrency.value; i++) {
    reqs.push(infra.ping().catch(() => {}))
  }
  await Promise.all(reqs)
}

function toggleLoadTest() {
  loadTesting.value = !loadTesting.value
  if (loadTesting.value) {
    sendBurst()
    loadTimer = setInterval(sendBurst, 1500)
  } else if (loadTimer) {
    clearInterval(loadTimer)
    loadTimer = null
  }
}

async function singlePing() {
  await infra.ping()
}

async function drain(id) {
  drainingId.value = id
  try {
    await infra.drainInstance(id)
  } finally {
    drainingId.value = ''
  }
}

async function deregister(id) {
  if (!confirm(`${id} ni ro'yxatdan o'chiramizmi?`)) return
  removingId.value = id
  try {
    await infra.deregisterInstance(id)
  } catch (e) {
    alert(e.response?.data?.detail || "O'chirib bo'lmadi")
  } finally {
    removingId.value = ''
  }
}

function timeAgo(iso) {
  const secs = Math.round((Date.now() - new Date(iso + 'Z').getTime()) / 1000)
  if (secs < 60) return `${secs}s oldin`
  return `${Math.round(secs / 60)}d oldin`
}

const scaleStatus = computed(() => {
  if (control.busy) return "Miqyoslanmoqda..."
  if (control.autoscaler.in_cooldown) return 'Cooldown'
  if (control.autoscaler.enabled) return "Avto miqyoslash yoqilgan"
  return 'Tayyor'
})

onMounted(async () => {
  await refresh()
  firstLoad.value = false
  refreshTimer = setInterval(refresh, REFRESH_MS)
})

onBeforeUnmount(() => {
  if (refreshTimer) clearInterval(refreshTimer)
  if (loadTimer) clearInterval(loadTimer)
})
</script>

<template>
  <div>
    <header class="page-head">
      <div>
        <h1>Infratuzilma</h1>
        <p class="text-muted small">{{ scaleStatus }}</p>
      </div>
      <div class="head-status">
        <span class="live-dot" :class="{ paused: control.busy }"></span>
        <span class="live-label small text-muted">
          {{ control.busy ? "Pauza (amal davom etmoqda)" : "Jonli yangilanmoqda" }}
        </span>
      </div>
    </header>

    <!-- KPI -->
    <div class="kpi-row">
      <div class="kpi card">
        <Icon name="server" :size="18" class="text-accent" />
        <div>
          <div class="kpi-value mono">{{ healthyCount }}/{{ infra.instances.length }}</div>
          <div class="kpi-label">Sog'lom instance'lar</div>
        </div>
      </div>
      <div class="kpi card">
        <Icon name="activity" :size="18" class="text-accent" />
        <div>
          <div class="kpi-value mono">{{ totalRequests }}</div>
          <div class="kpi-label">Jami so'rovlar</div>
        </div>
      </div>
      <div class="kpi card">
        <Icon name="globe" :size="18" class="text-accent" />
        <div>
          <div class="kpi-value mono">{{ control.autoscaler.current_rps_per_instance || 0 }}</div>
          <div class="kpi-label">Rps / instance</div>
        </div>
      </div>
      <div class="kpi card">
        <Icon name="zap" :size="18" class="text-accent" />
        <div>
          <div class="kpi-value mono">{{ infra.pingLog.length }}</div>
          <div class="kpi-label">Yuk test so'rovlari (oxirgi)</div>
        </div>
      </div>
    </div>

    <div class="infra-grid">
      <!-- Topology -->
      <div class="card topo-card">
        <div class="card-head">
          <h3><Icon name="network" :size="16" /> Tarmoq Topologiyasi</h3>
        </div>
        <NetworkTopology :topology="infra.topology" />
      </div>

      <!-- Load test -->
      <div class="card lb-card">
        <div class="card-head">
          <h3><Icon name="zap" :size="16" /> Yuk Sinovi</h3>
        </div>

        <div class="form-group">
          <label class="field-label">Burst'dagi parallel so'rov</label>
          <input class="input" type="number" min="1" max="200" v-model.number="concurrency" />
        </div>

        <div class="lb-actions">
          <button class="btn btn-secondary btn-sm" @click="singlePing">Bitta so'rov</button>
          <button class="btn btn-primary btn-sm" :class="{ active: loadTesting }" @click="toggleLoadTest">
            <Icon name="zap" :size="15" />
            {{ loadTesting ? "Yuk to'xtatish" : 'Yuk yuborish' }}
          </button>
          <button class="btn btn-ghost btn-sm" @click="infra.clearLog()">Tozalash</button>
        </div>

        <div class="dist">
          <div class="dist-head small text-muted">
            So'rov taqsimoti (oxirgi {{ infra.pingLog.length }})
          </div>
          <div v-for="d in distribution" :key="d.id" class="dist-row">
            <span class="mono dist-id">{{ d.id }}</span>
            <div class="dist-bar-track">
              <div class="dist-bar" :style="{ width: d.pct + '%' }"></div>
            </div>
            <span class="mono dist-count">{{ d.count }} ({{ d.pct }}%)</span>
          </div>
          <div v-if="distribution.length === 0" class="text-muted small empty-dist">
            Hozircha so'rov yuborilmagan.
          </div>
        </div>
      </div>
    </div>

    <!-- Scaling -->
    <div class="card scale-card">
      <div class="card-head">
        <h3><Icon name="server" :size="16" /> Instance Miqyoslash</h3>
        <span class="text-muted small">
          Chegaralar: min {{ control.limits.min }} · max {{ control.limits.max }}
        </span>
      </div>

      <div class="scale-grid">
        <!-- Manual -->
        <div class="scale-block">
          <div class="scale-label">Qo'lda miqyoslash</div>
          <div class="scaler">
            <button
              class="btn btn-secondary scale-btn"
              :disabled="control.busy || control.count <= control.limits.min"
              @click="control.scaleDown()"
              aria-label="Kamaytirish"
            >−</button>
            <div class="scale-count">
              <div class="scale-num mono">
                <span v-if="control.busy" class="spinner-inline"></span>
                <span v-else>{{ control.count }}</span>
              </div>
              <div class="scale-sub text-muted">instance</div>
            </div>
            <button
              class="btn btn-primary scale-btn"
              :disabled="control.busy || control.count >= control.limits.max"
              @click="control.scaleUp()"
              aria-label="Ko'paytirish"
            >+</button>
          </div>
          <div class="quick-set">
            <button
              v-for="n in quickTargets"
              :key="n"
              class="btn btn-ghost btn-sm"
              :class="{ 'quick-active': control.count === n }"
              :disabled="control.busy"
              @click="control.scaleTo(n)"
            >{{ n }}</button>
          </div>
        </div>

        <!-- Autoscaler -->
        <div class="scale-block">
          <div class="scale-label">
            Avto miqyoslash
            <label class="switch">
              <input
                type="checkbox"
                :checked="control.autoscaler.enabled"
                :disabled="control.busy"
                @change="control.toggleAutoscaler($event.target.checked)"
              />
              <span class="slider"></span>
            </label>
          </div>
          <div class="auto-status">
            <span class="badge" :class="control.autoscaler.enabled ? 'badge-green' : 'badge-gray'">
              {{ control.autoscaler.enabled ? 'Faol' : "O'chiq" }}
            </span>
            <span v-if="control.autoscaler.in_cooldown" class="badge badge-amber">cooldown</span>
          </div>
          <ul class="auto-meta">
            <li>
              <span class="text-muted">Yuklama:</span>
              <span class="mono">{{ control.autoscaler.current_rps_per_instance }} rps/inst</span>
            </li>
            <li>
              <span class="text-muted">Ko'paytirish &gt;</span>
              <span class="mono">{{ control.autoscaler.target_rps_high }}</span>
              <span class="text-muted"> · Kamaytirish &lt;</span>
              <span class="mono">{{ control.autoscaler.target_rps_low }}</span>
            </li>
            <li>
              <span class="text-muted">Cooldown:</span>
              <span class="mono">{{ control.autoscaler.cooldown_seconds }}s</span>
            </li>
            <li class="auto-reason text-muted">{{ control.autoscaler.last_reason }}</li>
          </ul>
        </div>
      </div>

      <p v-if="control.error" class="text-danger small scale-err">{{ control.error }}</p>
    </div>

    <!-- Instances table -->
    <div class="card table-card">
      <div class="card-head padded">
        <h3>
          <Icon name="server" :size="16" /> Backend Instance'lar
          <span v-if="control.busy" class="busy-pill">
            <span class="spinner-inline tiny"></span>
            Miqyoslanmoqda
          </span>
        </h3>
      </div>
      <table class="table">
        <thead>
          <tr>
            <th>Instance ID</th>
            <th>Zona</th>
            <th>Holat</th>
            <th>So'rovlar</th>
            <th>Oxirgi ko'rilgan</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="firstLoad && infra.instances.length === 0">
            <td colspan="6" class="empty">
              <span class="spinner-inline"></span> Yuklanmoqda...
            </td>
          </tr>
          <tr v-for="i in infra.instances" :key="i.instance_id" :class="{ removing: removingId === i.instance_id }">
            <td class="mono"><strong>{{ i.instance_id }}</strong></td>
            <td>{{ i.zone }}</td>
            <td>
              <span class="badge" :class="i.status === 'healthy' ? 'badge-green' : 'badge-red'">
                <span class="dot" :class="i.status"></span>
                {{ i.status === 'healthy' ? "Sog'lom" : 'Nosog\'lom' }}
              </span>
            </td>
            <td class="mono">{{ i.request_count }}</td>
            <td class="text-muted small">{{ timeAgo(i.last_seen) }}</td>
            <td>
              <div class="row-actions">
                <button
                  class="btn btn-ghost btn-sm"
                  :disabled="drainingId === i.instance_id"
                  @click="drain(i.instance_id)"
                >
                  <span v-if="drainingId === i.instance_id" class="spinner-inline tiny"></span>
                  Drain
                </button>
                <button
                  class="btn btn-ghost btn-sm text-danger"
                  :disabled="removingId === i.instance_id"
                  @click="deregister(i.instance_id)"
                  aria-label="O'chirish"
                >
                  <span v-if="removingId === i.instance_id" class="spinner-inline tiny"></span>
                  <Icon v-else name="trash" :size="15" />
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="!firstLoad && infra.instances.length === 0">
            <td colspan="6" class="empty">Instance topilmadi.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Animatsion layer diagrammasi -->
    <div class="card layers-card">
      <div class="card-head">
        <h3><Icon name="network" :size="16" /> Loyiha qatlamlari</h3>
        <span class="small text-muted">Ma'lumot oqimi: foydalanuvchi → nginx → api → DB</span>
      </div>
      <LayerDiagram
        :instance-count="infra.instances.length"
        :healthy-count="healthyCount"
        :total-requests="totalRequests"
        :active="loadTesting || totalRequests > 0"
      />
    </div>
  </div>
</template>

<style scoped>
.page-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: var(--space-lg);
  gap: var(--space-md);
  flex-wrap: wrap;
}
.page-head h1 { font-size: 24px; }
.head-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 999px;
  background: var(--color-muted, #f1f5f9);
}
.live-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: var(--color-accent, #059669);
  box-shadow: 0 0 0 0 rgba(5,150,105,0.6);
  animation: live-pulse 1.6s ease-out infinite;
}
.live-dot.paused {
  background: #f59e0b;
  animation: none;
}
@keyframes live-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(5,150,105,0.5); }
  50% { box-shadow: 0 0 0 6px rgba(5,150,105,0); }
}

.kpi-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--space-md);
  margin-bottom: var(--space-md);
}
.kpi { display: flex; align-items: center; gap: var(--space-md); }
.kpi-value { font-size: 20px; font-weight: 700; }
.kpi-label { font-size: 13px; color: var(--color-muted-foreground); }

.infra-grid {
  display: grid;
  grid-template-columns: 1.5fr 1fr;
  gap: var(--space-md);
  margin-bottom: var(--space-md);
}
.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-md);
  gap: var(--space-sm);
  flex-wrap: wrap;
}
.card-head.padded { padding: var(--space-md) var(--space-md) 0; margin-bottom: 0; }
.card-head h3 { font-size: 15px; display: flex; align-items: center; gap: 6px; }
.small { font-size: 12px; }
.lb-actions { display: flex; gap: var(--space-sm); flex-wrap: wrap; margin: var(--space-md) 0; }
.btn.active { background: var(--color-destructive); }
.form-group { margin-bottom: var(--space-sm); }
.dist { margin-top: var(--space-md); border-top: 1px solid var(--color-border); padding-top: var(--space-md); }
.dist-head { margin-bottom: var(--space-sm); }
.dist-row {
  display: grid;
  grid-template-columns: 110px 1fr 80px;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: 6px;
  font-size: 12px;
}
.dist-id { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.dist-bar-track { background: var(--color-muted); border-radius: 999px; height: 8px; overflow: hidden; }
.dist-bar { background: var(--color-accent); height: 100%; border-radius: 999px; transition: width 300ms ease; }
.dist-count { text-align: right; color: var(--color-muted-foreground); }
.empty-dist { padding: var(--space-sm) 0; }

.table-card { padding: 0; overflow: hidden; }
.row-actions { display: flex; gap: 4px; justify-content: flex-end; }
.empty { text-align: center; color: var(--color-muted-foreground); padding: var(--space-xl); }
.dot {
  width: 7px; height: 7px; border-radius: 50%; display: inline-block; margin-right: 4px;
}
.dot.healthy { background: #059669; }
.dot.unhealthy { background: #dc2626; }
tr.removing { opacity: 0.4; transition: opacity 200ms ease; }
.busy-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 999px;
  background: rgba(245, 158, 11, 0.15);
  color: #b45309;
  font-weight: 600;
  margin-left: 10px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

/* Scaling block */
.scale-card { margin-bottom: var(--space-md); }
.scale-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-lg);
}
.scale-block {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-md);
}
.scale-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  font-weight: 600;
  margin-bottom: var(--space-md);
}
.scaler {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-lg);
}
.scale-btn {
  width: 44px;
  height: 44px;
  font-size: 22px;
  line-height: 1;
  padding: 0;
  border-radius: 10px;
}
.scale-count { text-align: center; min-width: 80px; }
.scale-num {
  font-size: 32px;
  font-weight: 700;
  line-height: 1;
  min-height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.scale-sub { font-size: 12px; }
.quick-set {
  display: flex;
  gap: 4px;
  justify-content: center;
  margin-top: var(--space-md);
  flex-wrap: wrap;
}
.quick-set .btn { min-width: 34px; border: 1px solid var(--color-border); }
.quick-active { background: var(--color-primary); color: #fff; }
.auto-status { display: flex; gap: var(--space-sm); margin-bottom: var(--space-md); }
.auto-meta { list-style: none; display: flex; flex-direction: column; gap: 6px; font-size: 13px; }
.auto-reason { font-size: 12px; font-style: italic; }
.scale-err { margin-top: var(--space-md); }

/* Toggle */
.switch { position: relative; display: inline-block; width: 40px; height: 22px; }
.switch input { opacity: 0; width: 0; height: 0; }
.slider {
  position: absolute;
  cursor: pointer;
  inset: 0;
  background: #cbd5e1;
  border-radius: 999px;
  transition: background 200ms ease;
}
.slider::before {
  content: '';
  position: absolute;
  height: 16px;
  width: 16px;
  left: 3px;
  bottom: 3px;
  background: #fff;
  border-radius: 50%;
  transition: transform 200ms ease;
}
.switch input:checked + .slider { background: var(--color-accent); }
.switch input:checked + .slider::before { transform: translateX(18px); }

/* Spinner */
.spinner-inline {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-primary, #2563eb);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  vertical-align: middle;
}
.spinner-inline.tiny { width: 12px; height: 12px; border-width: 2px; margin-right: 4px; }
@keyframes spin { to { transform: rotate(360deg); } }

.layers-card { margin-top: var(--space-md); }

@media (max-width: 900px) {
  .infra-grid { grid-template-columns: 1fr; }
  .scale-grid { grid-template-columns: 1fr; }
}
</style>
