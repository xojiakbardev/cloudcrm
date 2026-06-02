import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api/client'

export const useControlStore = defineStore('control', () => {
  const count = ref(0)
  const limits = ref({ min: 1, max: 6 })
  const autoscaler = ref({
    enabled: false,
    in_cooldown: false,
    current_rps_per_instance: 0,
    last_reason: 'idle',
    min_instances: 1,
    max_instances: 6,
  })
  const busy = ref(false)
  const error = ref('')

  async function fetchStatus() {
    const { data } = await api.get('/control/status')
    count.value = data.count
    limits.value = data.limits
    autoscaler.value = data.autoscaler
    return data
  }

  async function _action(fn) {
    busy.value = true
    error.value = ''
    try {
      await fn()
      await fetchStatus()
    } catch (e) {
      error.value = e.response?.data?.detail || 'Action failed'
    } finally {
      busy.value = false
    }
  }

  function scaleUp() {
    return _action(() => api.post('/control/scale/up'))
  }

  function scaleDown() {
    return _action(() => api.post('/control/scale/down'))
  }

  function scaleTo(target) {
    return _action(() => api.post('/control/scale', { target }))
  }

  function toggleAutoscaler(enabled) {
    return _action(() => api.post('/control/autoscaler', { enabled }))
  }

  return {
    count,
    limits,
    autoscaler,
    busy,
    error,
    fetchStatus,
    scaleUp,
    scaleDown,
    scaleTo,
    toggleAutoscaler,
  }
})
