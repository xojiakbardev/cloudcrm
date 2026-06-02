import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api/client'

export const useInfraStore = defineStore('infra', () => {
  const instances = ref([])
  const topology = ref({ nodes: [], edges: [] })
  // Rolling log of which instance served recent ping requests.
  const pingLog = ref([])

  async function fetchInstances() {
    const { data } = await api.get('/infrastructure/instances')
    instances.value = data
    return data
  }

  async function fetchTopology() {
    const { data } = await api.get('/infrastructure/topology')
    topology.value = data
    return data
  }

  async function ping() {
    const { data } = await api.get('/infrastructure/ping')
    pingLog.value.unshift({ ...data, at: Date.now() })
    if (pingLog.value.length > 50) pingLog.value.pop()
    return data
  }

  async function drainInstance(id) {
    await api.post(`/infrastructure/instances/${id}/drain`)
    await fetchInstances()
    await fetchTopology()
  }

  async function deregisterInstance(id) {
    await api.delete(`/infrastructure/instances/${id}`)
    await fetchInstances()
    await fetchTopology()
  }

  function clearLog() {
    pingLog.value = []
  }

  return {
    instances,
    topology,
    pingLog,
    fetchInstances,
    fetchTopology,
    ping,
    drainInstance,
    deregisterInstance,
    clearLog,
  }
})
