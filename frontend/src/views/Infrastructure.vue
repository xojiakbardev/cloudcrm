<script setup>
import { onMounted, onBeforeUnmount, ref, computed } from 'vue'
import { useInfraStore } from '../stores/infra'
import { useControlStore } from '../stores/control'
import NetworkTopology from '../components/NetworkTopology.vue'
import Icon from '../components/Icon.vue'

const infra = useInfraStore()
const control = useControlStore()

const autoRefresh = ref(true)
const loadTesting = ref(false)
const concurrency = ref(20)
let refreshTimer = null
let loadTimer = null

const healthyCount = computed(() => infra.instances.filter((i) => i.status === 'healthy').length)
const totalRequests = computed(() => infra.instances.reduce((s, i) => s + i.request_count, 0))

// Quick-set scale targets between min and max.
const quickTargets = computed(() => {
  const out = []
  for (let n = control.limits.min; n <= control.limits.max; n++) out.push(n)
  return out
})

// Distribution of recent pings across instances (proves round-robin balancing).
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
  await Promise.all([infra.fetchInstances(), infra.fetchTopology(), control.fetchStatus()])
}

function toggleAutoRefresh() {
  autoRefresh.value = !autoRefresh.value
  setupRefresh()
}

function setupRefresh() {
  if (refreshTimer) clearInterval(refreshTimer)
  if (autoRefresh.value) {
    refreshTimer = setInterval(refresh, 3000)
  }
}

// Fire a burst of concurrent pings through the load balancer to generate load.
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
  }
}

async function singlePing() {
  await infra.ping()
}

async function drain(id) {
  await infra.drainInstance(id)
}

async function deregister(id) {
  if (confirm(`Deregister instance ${id} from the load balancer?`)) {
    await infra.deregisterInstance(id)
  }
}

function timeAgo(iso) {
  const secs = Math.round((Date.now() - new Date(iso + 'Z').getTime()) / 1000)
  if (secs < 60) return `${secs}s ago`
  return `${Math.round(secs / 60)}m ago`
}

onMounted(async () => {
  await refresh()
  setupRefresh()
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
        <h1>Infrastructure</h1>
      </div>
      <div class="head-actions">
        <button class="btn btn-secondary btn-sm" @click="toggleAutoRefresh">
          <Icon name="refresh" :size="15" />
          {{ autoRefresh ? 'Auto-refresh: On' : 'Auto-refresh: Off' }}
        </button>
        <button class="btn btn-secondary btn-sm" @click="refresh">
          <Icon name="refresh" :size="15" /> Refresh now
        </button>
      </div>
    </header>

    <!-- Summary KPIs -->
    <div class="kpi-row">
      <div class="kpi card">
        <Icon name="server" :size="18" class="text-accent" />
        <div><div class="kpi-value mono">{{ healthyCount }}/{{ infra.instances.length }}</div>
        <div class="kpi-label">Healthy instances</div></div>
      </div>
      <div class="kpi card">
        <Icon name="activity" :size="18" class="text-accent" />
        <div><div class="kpi-value mono">{{ totalRequests }}</div>
        <div class="kpi-label">Total requests served</div></div>
      </div>
      <div class="kpi card">
        <Icon name="globe" :size="18" class="text-accent" />
        <div><div class="kpi-value mono">round-robin</div>
        <div class="kpi-label">LB algorithm (Nginx)</div></div>
      </div>
    </div>

    <div class="infra-grid">
      <!-- Topology -->
      <div class="card topo-card">
        <div class="card-head">
          <h3><Icon name="network" :size="16" /> Network Topology</h3>
          <span class="text-muted small">Gateway → Load Balancer → Instances → Database</span>
        </div>
        <NetworkTopology :topology="infra.topology" />
      </div>

      <!-- Load balancer control -->
      <div class="card lb-card">
        <div class="card-head">
          <h3><Icon name="zap" :size="16" /> Load Test</h3>
        </div>
        <p class="text-muted small">
          Send requests through the Nginx load balancer and watch them spread across instances.
        </p>

        <div class="form-group">
          <label class="field-label">Concurrent requests per burst</label>
          <input class="input" type="number" min="1" max="200" v-model.number="concurrency" />
        </div>

        <div class="lb-actions">
          <button class="btn btn-secondary btn-sm" @click="singlePing">Single request</button>
          <button class="btn btn-primary btn-sm" :class="{ active: loadTesting }" @click="toggleLoadTest">
            <Icon name="zap" :size="15" />
            {{ loadTesting ? 'Stop load' : 'Start load' }}
          </button>
          <button class="btn btn-ghost btn-sm" @click="infra.clearLog()">Clear</button>
        </div>

        <div class="dist">
          <div class="dist-head small text-muted">
            Request distribution (last {{ infra.pingLog.length }})
          </div>
          <div v-for="d in distribution" :key="d.id" class="dist-row">
            <span class="mono dist-id">{{ d.id }}</span>
            <div class="dist-bar-track">
              <div class="dist-bar" :style="{ width: d.pct + '%' }"></div>
            </div>
            <span class="mono dist-count">{{ d.count }} ({{ d.pct }}%)</span>
          </div>
          <div v-if="distribution.length === 0" class="text-muted small empty-dist">
            No requests sent yet.
          </div>
        </div>
      </div>
    </div>

    <!-- Scaling control plane -->
    <div class="card scale-card">
      <div class="card-head">
        <h3><Icon name="server" :size="16" /> Instance Scaling</h3>
        <span class="text-muted small">
          Limits: min {{ control.limits.min }} · max {{ control.limits.max }}
        </span>
      </div>

      <div class="scale-grid">
        <!-- Manual scaling -->
        <div class="scale-block">
          <div class="scale-label">Manual scaling</div>
          <div class="scaler">
            <button
              class="btn btn-secondary scale-btn"
              :disabled="control.busy || control.count <= control.limits.min"
              @click="control.scaleDown()"
              aria-label="Scale down"
            >−</button>
            <div class="scale-count">
              <div class="scale-num mono">{{ control.count }}</div>
              <div class="scale-sub text-muted">instances</div>
            </div>
            <button
              class="btn btn-primary scale-btn"
              :disabled="control.busy || control.count >= control.limits.max"
              @click="control.scaleUp()"
              aria-label="Scale up"
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
            Autoscaler
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
              {{ control.autoscaler.enabled ? 'Active' : 'Off' }}
            </span>
            <span v-if="control.autoscaler.in_cooldown" class="badge badge-amber">cooldown</span>
          </div>
          <ul class="auto-meta">
            <li><span class="text-muted">Load:</span> <span class="mono">{{ control.autoscaler.current_rps_per_instance }} rps/inst</span></li>
            <li><span class="text-muted">Scale up &gt;</span> <span class="mono">{{ control.autoscaler.target_rps_high }}</span> · <span class="text-muted">down &lt;</span> <span class="mono">{{ control.autoscaler.target_rps_low }}</span></li>
            <li><span class="text-muted">Cooldown:</span> <span class="mono">{{ control.autoscaler.cooldown_seconds }}s</span></li>
            <li class="auto-reason text-muted">{{ control.autoscaler.last_reason }}</li>
          </ul>
        </div>
      </div>

      <p v-if="control.error" class="text-danger small scale-err">{{ control.error }}</p>
    </div>

    <!-- Instances table -->
    <div class="card table-card">
      <div class="card-head padded">
        <h3><Icon name="server" :size="16" /> Backend Instances</h3>
        <span class="text-muted small">Managed by the control plane · scale with the buttons above</span>
      </div>
      <table class="table">
        <thead>
          <tr>
            <th>Instance ID</th>
            <th>Zone</th>
            <th>Status</th>
            <th>Requests</th>
            <th>Last seen</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="i in infra.instances" :key="i.instance_id">
            <td class="mono"><strong>{{ i.instance_id }}</strong></td>
            <td>{{ i.zone }}</td>
            <td>
              <span class="badge" :class="i.status === 'healthy' ? 'badge-green' : 'badge-red'">
                <span class="dot" :class="i.status"></span>{{ i.status }}
              </span>
            </td>
            <td class="mono">{{ i.request_count }}</td>
            <td class="text-muted small">{{ timeAgo(i.last_seen) }}</td>
            <td>
              <div class="row-actions">
                <button class="btn btn-ghost btn-sm" @click="drain(i.instance_id)" title="Drain (mark unhealthy)">Drain</button>
                <button class="btn btn-ghost btn-sm text-danger" @click="deregister(i.instance_id)" aria-label="Deregister">
                  <Icon name="trash" :size="15" />
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="infra.instances.length === 0">
            <td colspan="6" class="empty">No instances registered.</td>
          </tr>
        </tbody>
      </table>
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
.head-actions { display: flex; gap: var(--space-sm); }
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

/* ---- Scaling control ---- */
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
.scale-num { font-size: 32px; font-weight: 700; line-height: 1; }
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

/* Toggle switch */
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

@media (max-width: 900px) {
  .infra-grid { grid-template-columns: 1fr; }
  .scale-grid { grid-template-columns: 1fr; }
}
</style>
