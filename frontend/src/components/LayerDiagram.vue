<script setup>
import { computed } from 'vue'

const props = defineProps({
  instanceCount: { type: Number, default: 0 },
  healthyCount: { type: Number, default: 0 },
  totalRequests: { type: Number, default: 0 },
  active: { type: Boolean, default: false },
})

// Cap visual instance boxes at 6 so the diagram stays readable.
const visible = computed(() => Math.min(Math.max(props.instanceCount, 1), 6))
const instances = computed(() => {
  const out = []
  for (let i = 0; i < visible.value; i++) {
    out.push({
      n: i + 1,
      healthy: i < props.healthyCount,
    })
  }
  return out
})
</script>

<template>
  <div class="diagram" :class="{ flowing: active }">
    <!-- Foydalanuvchi qatlami -->
    <div class="layer">
      <div class="layer-label">Foydalanuvchilar</div>
      <div class="nodes">
        <div class="node user" v-for="n in 3" :key="n">
          <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="8" r="4"/>
            <path d="M4 20c0-4 4-6 8-6s8 2 8 6"/>
          </svg>
        </div>
      </div>
    </div>
    <div class="pipe">
      <div class="arrow"></div>
      <div class="particle p1"></div>
      <div class="particle p2"></div>
      <div class="particle p3"></div>
      <span class="pipe-label">HTTPS / 443</span>
    </div>

    <!-- DNS / Internet kirish -->
    <div class="layer">
      <div class="layer-label">Reverse Proxy + Yuk Taqsimlovchi</div>
      <div class="nodes">
        <div class="node gateway">
          <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <path d="M2 12h20M12 2a15 15 0 0 1 0 20M12 2a15 15 0 0 0 0 20"/>
          </svg>
          <span>Nginx</span>
        </div>
      </div>
    </div>
    <div class="pipe">
      <div class="arrow forked"></div>
      <div class="particle p1"></div>
      <div class="particle p2"></div>
      <div class="particle p3"></div>
      <span class="pipe-label">least_conn · round-robin</span>
    </div>

    <!-- API qatlami -->
    <div class="layer">
      <div class="layer-label">API Instance'lari ({{ healthyCount }}/{{ instanceCount }} sog'lom)</div>
      <div class="nodes wide">
        <div
          v-for="i in instances"
          :key="i.n"
          class="node api"
          :class="{ unhealthy: !i.healthy }"
        >
          <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="4" width="18" height="6" rx="2"/>
            <rect x="3" y="14" width="18" height="6" rx="2"/>
            <circle cx="7" cy="7" r="1" fill="currentColor"/>
            <circle cx="7" cy="17" r="1" fill="currentColor"/>
          </svg>
          <span>api-{{ i.n }}</span>
        </div>
      </div>
    </div>
    <div class="pipe">
      <div class="arrow converging"></div>
      <div class="particle p1"></div>
      <div class="particle p2"></div>
      <span class="pipe-label">SQL · 5432</span>
    </div>

    <!-- Ma'lumotlar qatlami -->
    <div class="layer">
      <div class="layer-label">Ma'lumotlar Bazasi</div>
      <div class="nodes">
        <div class="node db">
          <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2">
            <ellipse cx="12" cy="5" rx="9" ry="3"/>
            <path d="M3 5v6c0 1.7 4 3 9 3s9-1.3 9-3V5"/>
            <path d="M3 11v6c0 1.7 4 3 9 3s9-1.3 9-3v-6"/>
          </svg>
          <span>PostgreSQL 16</span>
        </div>
      </div>
    </div>

    <!-- Statistika ostida -->
    <div class="stats-strip">
      <div class="stat">
        <span class="stat-num">{{ instanceCount }}</span>
        <span class="stat-label">Instance soni</span>
      </div>
      <div class="stat">
        <span class="stat-num">{{ healthyCount }}</span>
        <span class="stat-label">Sog'lom</span>
      </div>
      <div class="stat">
        <span class="stat-num">{{ totalRequests }}</span>
        <span class="stat-label">Jami so'rovlar</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.diagram {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: var(--space-lg) var(--space-md);
}
.layer {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}
.layer-label {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-muted-foreground);
  font-weight: 600;
}
.nodes {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
}
.nodes.wide { gap: 10px; }
.node {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border-radius: 10px;
  background: var(--color-surface, #fff);
  border: 1.5px solid var(--color-border);
  font-size: 13px;
  font-weight: 600;
  font-family: var(--font-mono, ui-monospace, monospace);
  box-shadow: 0 1px 2px rgba(0,0,0,0.04);
  transition: transform 200ms ease, box-shadow 200ms ease, border-color 200ms ease;
  position: relative;
}
.diagram.flowing .node {
  animation: pulse 1.6s ease-in-out infinite;
}
.node.user {
  padding: 8px;
  color: #2563eb;
  border-color: #93c5fd;
  background: #eff6ff;
}
.node.gateway {
  color: #059669;
  border-color: #6ee7b7;
  background: #ecfdf5;
}
.node.api {
  color: #6366f1;
  border-color: #c7d2fe;
  background: #eef2ff;
}
.node.api.unhealthy {
  color: #94a3b8;
  border-color: #e2e8f0;
  background: #f8fafc;
  opacity: 0.5;
}
.node.db {
  color: #b45309;
  border-color: #fcd34d;
  background: #fffbeb;
  padding: 12px 20px;
}

/* ---- Pipes + animated particles flowing along the data path ---- */
.pipe {
  position: relative;
  width: 3px;
  height: 56px;
  background: linear-gradient(to bottom, var(--color-border), var(--color-border));
  margin: 4px 0;
  display: flex;
  justify-content: center;
}
.pipe-label {
  position: absolute;
  left: calc(50% + 16px);
  top: 50%;
  transform: translateY(-50%);
  font-size: 11px;
  font-family: var(--font-mono, monospace);
  color: var(--color-muted-foreground);
  white-space: nowrap;
}
.arrow {
  position: absolute;
  bottom: -4px;
  left: 50%;
  width: 10px;
  height: 10px;
  border-right: 2px solid var(--color-border);
  border-bottom: 2px solid var(--color-border);
  transform: translateX(-50%) rotate(45deg);
}
.particle {
  position: absolute;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-accent, #059669);
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  opacity: 0;
}
.diagram.flowing .particle {
  animation: flow 2.2s linear infinite;
  opacity: 1;
}
.diagram.flowing .particle.p1 { animation-delay: 0s; }
.diagram.flowing .particle.p2 { animation-delay: 0.7s; }
.diagram.flowing .particle.p3 { animation-delay: 1.4s; }
@keyframes flow {
  0%   { top: -4px;   opacity: 0; transform: translateX(-50%) scale(0.6); }
  10%  { opacity: 1; transform: translateX(-50%) scale(1); }
  90%  { opacity: 1; }
  100% { top: calc(100% - 4px); opacity: 0; transform: translateX(-50%) scale(0.6); }
}
@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(99,102,241,0); }
  50% { box-shadow: 0 0 0 6px rgba(99,102,241,0.12); }
}

.stats-strip {
  margin-top: var(--space-md);
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-md);
  width: 100%;
  max-width: 480px;
  border-top: 1px dashed var(--color-border);
  padding-top: var(--space-md);
}
.stat { text-align: center; }
.stat-num {
  display: block;
  font-size: 22px;
  font-weight: 700;
  font-family: var(--font-mono, monospace);
  color: var(--color-foreground);
}
.stat-label {
  display: block;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-muted-foreground);
  margin-top: 2px;
}

/* When dark mode flips, the bg colours stay readable */
@media (prefers-color-scheme: dark) {
  .node.user { background: rgba(59, 130, 246, 0.12); }
  .node.gateway { background: rgba(5, 150, 105, 0.12); }
  .node.api { background: rgba(99, 102, 241, 0.12); }
  .node.api.unhealthy { background: rgba(148, 163, 184, 0.08); }
  .node.db { background: rgba(180, 83, 9, 0.12); }
}
</style>
