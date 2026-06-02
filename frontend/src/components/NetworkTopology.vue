<script setup>
import { onMounted, onBeforeUnmount, ref, watch } from 'vue'
import { Network } from 'vis-network/standalone'

const props = defineProps({
  topology: { type: Object, required: true },
})

const container = ref(null)
let network = null

const NODE_STYLE = {
  gateway: { color: '#2563eb', shape: 'hexagon', icon: 'GW' },
  loadbalancer: { color: '#6366f1', shape: 'diamond', icon: 'LB' },
  instance: { color: '#059669', shape: 'box', icon: 'API' },
  database: { color: '#0f172a', shape: 'database', icon: 'DB' },
}

function buildData() {
  const nodes = props.topology.nodes.map((n) => {
    const style = NODE_STYLE[n.type] || {}
    const unhealthy = n.status === 'unhealthy'
    let title = `${n.label} (${n.type})`
    if (n.meta) {
      title += '\n' + Object.entries(n.meta).map(([k, v]) => `${k}: ${v}`).join('\n')
    }
    return {
      id: n.id,
      label: n.type === 'instance'
        ? `${n.label}\n${n.meta?.requests ?? 0} req · ${n.meta?.traffic_share ?? 0}%`
        : n.label,
      shape: style.shape || 'box',
      color: {
        background: unhealthy ? '#fee2e2' : '#ffffff',
        border: unhealthy ? '#dc2626' : (style.color || '#3b82f6'),
        highlight: { background: '#eff6ff', border: style.color || '#2563eb' },
      },
      borderWidth: 2,
      font: { color: '#0f172a', face: 'Fira Sans', multi: true, size: 13 },
      title,
      margin: 10,
    }
  })

  const edges = props.topology.edges.map((e) => ({
    from: e.source,
    to: e.target,
    label: e.label || '',
    arrows: 'to',
    color: { color: '#90a4ae', highlight: '#2563eb' },
    font: { color: '#64748b', size: 11, strokeWidth: 3, strokeColor: '#ffffff' },
    smooth: { type: 'cubicBezier', forceDirection: 'vertical', roundness: 0.5 },
  }))

  return { nodes, edges }
}

function render() {
  if (!container.value) return
  const data = buildData()
  const options = {
    layout: {
      hierarchical: {
        enabled: true,
        direction: 'UD',
        sortMethod: 'directed',
        levelSeparation: 110,
        nodeSpacing: 140,
      },
    },
    physics: { enabled: false },
    interaction: { hover: true, dragNodes: true, zoomView: true },
  }
  if (network) {
    network.setData(data)
  } else {
    network = new Network(container.value, data, options)
  }
}

watch(() => props.topology, render, { deep: true })
onMounted(render)
onBeforeUnmount(() => {
  if (network) network.destroy()
})
</script>

<template>
  <div ref="container" class="topology"></div>
</template>

<style scoped>
.topology {
  height: 420px;
  width: 100%;
  background:
    linear-gradient(90deg, rgba(226, 232, 240, 0.4) 1px, transparent 1px),
    linear-gradient(rgba(226, 232, 240, 0.4) 1px, transparent 1px);
  background-size: 24px 24px;
  border-radius: var(--radius-md);
}
</style>
