import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api/client'

export const useCrmStore = defineStore('crm', () => {
  const customers = ref([])
  const deals = ref([])
  const stats = ref(null)

  async function fetchCustomers(params = {}) {
    const { data } = await api.get('/customers', { params })
    customers.value = data
    return data
  }

  async function createCustomer(payload) {
    const { data } = await api.post('/customers', payload)
    customers.value.unshift(data)
    return data
  }

  async function updateCustomer(id, payload) {
    const { data } = await api.put(`/customers/${id}`, payload)
    const idx = customers.value.findIndex((c) => c.id === id)
    if (idx !== -1) customers.value[idx] = data
    return data
  }

  async function deleteCustomer(id) {
    await api.delete(`/customers/${id}`)
    customers.value = customers.value.filter((c) => c.id !== id)
  }

  async function fetchDeals(params = {}) {
    const { data } = await api.get('/deals', { params })
    deals.value = data
    return data
  }

  async function createDeal(payload) {
    const { data } = await api.post('/deals', payload)
    deals.value.unshift(data)
    return data
  }

  async function updateDeal(id, payload) {
    const { data } = await api.put(`/deals/${id}`, payload)
    const idx = deals.value.findIndex((d) => d.id === id)
    if (idx !== -1) deals.value[idx] = data
    return data
  }

  async function deleteDeal(id) {
    await api.delete(`/deals/${id}`)
    deals.value = deals.value.filter((d) => d.id !== id)
  }

  async function fetchStats() {
    const { data } = await api.get('/dashboard/stats')
    stats.value = data
    return data
  }

  return {
    customers,
    deals,
    stats,
    fetchCustomers,
    createCustomer,
    updateCustomer,
    deleteCustomer,
    fetchDeals,
    createDeal,
    updateDeal,
    deleteDeal,
    fetchStats,
  }
})
