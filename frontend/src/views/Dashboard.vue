<script setup>
import { onMounted, ref, computed } from 'vue'
import { Chart, registerables } from 'chart.js'
import { useCrmStore } from '../stores/crm'
import StatCard from '../components/StatCard.vue'

Chart.register(...registerables)

const crm = useCrmStore()

// Canvas refs
const stageCanvas = ref(null)
const statusCanvas = ref(null)
const orderStatusCanvas = ref(null)
const revenueCanvas = ref(null)
const topProductsCanvas = ref(null)

// Chart instances
let stageChart = null
let statusChart = null
let orderStatusChart = null
let revenueChart = null
let topProductsChart = null

const stats = computed(() => crm.stats)

function money(v) {
  return '$' + Number(v || 0).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })
}

const STAGE_COLORS = {
  new: '#94a3b8',
  qualified: '#3b82f6',
  proposal: '#6366f1',
  won: '#059669',
  lost: '#dc2626',
}

const ORDER_COLORS = {
  pending: '#f59e0b',
  confirmed: '#3b82f6',
  shipped: '#6366f1',
  delivered: '#10b981',
  cancelled: '#ef4444',
}

const STATUS_UZ = {
  // Customers
  active: 'Faol',
  lead: 'Lead',
  inactive: 'Nofaol',
  // Deals
  new: 'Yangi',
  qualified: 'Saralangan',
  proposal: 'Taklif',
  won: 'Yutilgan',
  lost: 'Yo\'qotilgan',
  // Orders
  pending: 'Kutilmoqda',
  confirmed: 'Tasdiqlandi',
  shipped: 'Yuborildi',
  delivered: 'Yetkazildi',
  cancelled: 'Bekor qilindi',
}

const MONTH_NAMES = {
  '01': 'Yanvar', '02': 'Fevral', '03': 'Mart', '04': 'Aprel', '05': 'May', '06': 'Iyun',
  '07': 'Iyul', '08': 'Avgust', '09': 'Sentyabr', '10': 'Oktyabr', '11': 'Noyabr', '12': 'Dekabr'
}

// Computed stats
const totalOrders = computed(() => {
  if (!stats.value || !stats.value.orders_by_status) return 0
  return Object.values(stats.value.orders_by_status).reduce((sum, count) => sum + count, 0)
})

const totalRevenue = computed(() => {
  if (!stats.value || !stats.value.monthly_revenue) return 0
  return Object.values(stats.value.monthly_revenue).reduce((sum, rev) => sum + rev, 0)
})

function renderCharts() {
  if (!stats.value) return

  // 1. Deals Stage Bar Chart
  const stageKeys = Object.keys(stats.value.deals_by_stage)
  const stageLabels = stageKeys.map(k => STATUS_UZ[k] || k)
  const stageData = Object.values(stats.value.deals_by_stage)

  if (stageChart) stageChart.destroy()
  stageChart = new Chart(stageCanvas.value, {
    type: 'bar',
    data: {
      labels: stageLabels,
      datasets: [
        {
          label: 'Bitimlar',
          data: stageData,
          backgroundColor: stageKeys.map((s) => STAGE_COLORS[s] || '#3b82f6'),
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

  // 2. Customers Status Doughnut
  const statusKeys = Object.keys(stats.value.customers_by_status)
  const statusLabels = statusKeys.map(k => STATUS_UZ[k] || k)
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

  // 3. Orders Status Doughnut
  const orderStatusKeys = Object.keys(stats.value.orders_by_status || {})
  const orderStatusLabels = orderStatusKeys.map(k => STATUS_UZ[k] || k)
  const orderStatusData = Object.values(stats.value.orders_by_status || {})

  if (orderStatusChart) orderStatusChart.destroy()
  orderStatusChart = new Chart(orderStatusCanvas.value, {
    type: 'doughnut',
    data: {
      labels: orderStatusLabels,
      datasets: [
        {
          data: orderStatusData,
          backgroundColor: orderStatusKeys.map(s => ORDER_COLORS[s] || '#94a3b8'),
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: 'bottom' } },
    },
  })

  // 4. Monthly Revenue Line Chart
  const revenueKeys = Object.keys(stats.value.monthly_revenue || {}).sort()
  const revenueLabels = revenueKeys.map(k => {
    const [yr, mo] = k.split('-')
    return MONTH_NAMES[mo] ? `${MONTH_NAMES[mo]} ${yr}` : k
  })
  const revenueData = revenueKeys.map(k => stats.value.monthly_revenue[k])

  if (revenueChart) revenueChart.destroy()
  revenueChart = new Chart(revenueCanvas.value, {
    type: 'line',
    data: {
      labels: revenueLabels,
      datasets: [
        {
          label: 'Daromad ($)',
          data: revenueData,
          borderColor: '#2563eb',
          backgroundColor: 'rgba(37, 99, 235, 0.08)',
          fill: true,
          tension: 0.35,
          borderWidth: 2.5,
          pointBackgroundColor: '#2563eb',
          pointHoverRadius: 6,
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: (value) => '$' + Number(value).toLocaleString()
          }
        }
      }
    }
  })

  // 5. Top 5 Products Horizontal Bar Chart
  const productLabels = Object.keys(stats.value.top_products || {})
  const productData = Object.values(stats.value.top_products || {})

  if (topProductsChart) topProductsChart.destroy()
  topProductsChart = new Chart(topProductsCanvas.value, {
    type: 'bar',
    data: {
      labels: productLabels,
      datasets: [
        {
          label: 'Sotilgan dona',
          data: productData,
          backgroundColor: '#6366f1',
          borderRadius: 4,
          barThickness: 16,
        }
      ]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: {
          beginAtZero: true,
          ticks: { precision: 0 }
        }
      }
    }
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
        <h1>Boshqaruv paneli</h1>
      </div>
    </header>

    <div v-if="stats" class="stats-grid">
      <StatCard label="Jami mijozlar" :value="stats.total_customers" icon="users" accent="blue" />
      <StatCard label="Jami buyurtmalar" :value="totalOrders" icon="cart" accent="blue" />
      <StatCard label="Umumiy tushum" :value="money(totalRevenue)" icon="deals" accent="green" />
      <StatCard label="Yutilgan bitimlar" :value="money(stats.won_value)" icon="zap" accent="green" />
    </div>

    <!-- Main analytics dashboard charts -->
    <div class="charts-grid">
      <!-- Row 1: Line revenue chart and product leaderboards -->
      <div class="card col-8">
        <h3 class="chart-title">Oylik tushum trendi (so'nggi 6 oy)</h3>
        <div class="chart-box"><canvas ref="revenueCanvas"></canvas></div>
      </div>
      
      <div class="card col-4">
        <h3 class="chart-title">Top 5 mahsulotlar (sotuv hajmi)</h3>
        <div class="chart-box"><canvas ref="topProductsCanvas"></canvas></div>
      </div>

      <!-- Row 2: Status and pipeline breakdown -->
      <div class="card col-6">
        <h3 class="chart-title">Bosqich bo'yicha bitimlar</h3>
        <div class="chart-box"><canvas ref="stageCanvas"></canvas></div>
      </div>

      <div class="card col-3">
        <h3 class="chart-title">Mijozlar holati</h3>
        <div class="chart-box"><canvas ref="statusCanvas"></canvas></div>
      </div>

      <div class="card col-3">
        <h3 class="chart-title">Buyurtmalar holati</h3>
        <div class="chart-box"><canvas ref="orderStatusCanvas"></canvas></div>
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
  grid-template-columns: repeat(12, 1fr);
  gap: var(--space-md);
}
.chart-title {
  font-size: 15px;
  margin-bottom: var(--space-md);
  color: var(--color-foreground);
}
.chart-box {
  height: 280px;
  position: relative;
}

/* Grid columns layout */
.col-12 { grid-column: span 12; }
.col-8 { grid-column: span 8; }
.col-6 { grid-column: span 6; }
.col-4 { grid-column: span 4; }
.col-3 { grid-column: span 3; }

@media (max-width: 1024px) {
  .col-8, .col-6, .col-4, .col-3 {
    grid-column: span 6;
  }
}

@media (max-width: 768px) {
  .col-8, .col-6, .col-4, .col-3 {
    grid-column: span 12;
  }
}
</style>

