<script setup>
import { onMounted, ref, computed } from 'vue'
import { Chart, registerables } from 'chart.js'
import { useCrmStore } from '../stores/crm'
import StatCard from '../components/StatCard.vue'

Chart.register(...registerables)

const crm = useCrmStore()
const stageCanvas = ref(null)
const statusCanvas = ref(null)
let stageChart = null
let statusChart = null

const stats = computed(() => crm.stats)

function money(v) {
  return '$' + Number(v || 0).toLocaleString()
}

const STAGE_COLORS = {
  new: '#94a3b8',
  qualified: '#3b82f6',
  proposal: '#6366f1',
  won: '#059669',
  lost: '#dc2626',
}

function renderCharts() {
  if (!stats.value) return

  const stageLabels = Object.keys(stats.value.deals_by_stage)
  const stageData = Object.values(stats.value.deals_by_stage)

  if (stageChart) stageChart.destroy()
  stageChart = new Chart(stageCanvas.value, {
    type: 'bar',
    data: {
      labels: stageLabels,
      datasets: [
        {
          label: 'Deals',
          data: stageData,
          backgroundColor: stageLabels.map((s) => STAGE_COLORS[s] || '#3b82f6'),
          borderRadius: 6,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
    },
  })

  const statusLabels = Object.keys(stats.value.customers_by_status)
  const statusData = Object.values(stats.value.customers_by_status)

  if (statusChart) statusChart.destroy()
  statusChart = new Chart(statusCanvas.value, {
    type: 'doughnut',
    data: {
      labels: statusLabels,
      datasets: [
        {
          data: statusData,
          backgroundColor: ['#059669', '#3b82f6', '#dc2626', '#94a3b8'],
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: 'bottom' } },
    },
  })
}

onMounted(async () => {
  await crm.fetchStats()
  renderCharts()
})
</script>

<template>
  <div>
    <header class="page-head">
      <div>
        <h1>Dashboard</h1>
        <p class="text-muted">Sales pipeline overview</p>
      </div>
    </header>

    <div v-if="stats" class="stats-grid">
      <StatCard label="Total Customers" :value="stats.total_customers" icon="users" accent="blue" />
      <StatCard label="Active Customers" :value="stats.active_customers" icon="users" accent="green" />
      <StatCard label="Pipeline Value" :value="money(stats.pipeline_value)" icon="deals" accent="amber" />
      <StatCard label="Won Value" :value="money(stats.won_value)" icon="zap" accent="green" />
    </div>

    <div class="charts-grid">
      <div class="card">
        <h3 class="chart-title">Deals by Stage</h3>
        <div class="chart-box"><canvas ref="stageCanvas"></canvas></div>
      </div>
      <div class="card">
        <h3 class="chart-title">Customers by Status</h3>
        <div class="chart-box"><canvas ref="statusCanvas"></canvas></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-head {
  margin-bottom: var(--space-lg);
}
.page-head h1 { font-size: 24px; }
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
}
.charts-grid {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: var(--space-md);
}
.chart-title {
  font-size: 15px;
  margin-bottom: var(--space-md);
}
.chart-box {
  height: 280px;
}
@media (max-width: 900px) {
  .charts-grid { grid-template-columns: 1fr; }
}
</style>
