import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api/client'

export const useCrmStore = defineStore('crm', () => {
  const customers = ref([])
  const deals = ref([])
  const products = ref([])
  const orders = ref([])
  const stats = ref(null)

  // ── Customers ──────────────────────────────────────────────────────────
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

  // ── Deals ──────────────────────────────────────────────────────────────
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

  // ── Products ───────────────────────────────────────────────────────────
  async function fetchProducts(params = {}) {
    const { data } = await api.get('/products', { params })
    products.value = data
    return data
  }

  async function createProduct(payload) {
    const { data } = await api.post('/products', payload)
    products.value.unshift(data)
    return data
  }

  async function updateProduct(id, payload) {
    const { data } = await api.put(`/products/${id}`, payload)
    const idx = products.value.findIndex((p) => p.id === id)
    if (idx !== -1) products.value[idx] = data
    return data
  }

  async function deleteProduct(id) {
    await api.delete(`/products/${id}`)
    products.value = products.value.filter((p) => p.id !== id)
  }

  // ── Orders ─────────────────────────────────────────────────────────────
  async function fetchOrders(params = {}) {
    const { data } = await api.get('/orders', { params })
    orders.value = data
    return data
  }

  async function createOrder(payload) {
    const { data } = await api.post('/orders', payload)
    orders.value.unshift(data)
    return data
  }

  async function updateOrderStatus(id, status, notes = null) {
    const { data } = await api.patch(`/orders/${id}/status`, { status, notes })
    const idx = orders.value.findIndex((o) => o.id === id)
    if (idx !== -1) orders.value[idx] = data
    return data
  }

  async function deleteOrder(id) {
    await api.delete(`/orders/${id}`)
    orders.value = orders.value.filter((o) => o.id !== id)
  }

  // ── Dashboard ──────────────────────────────────────────────────────────
  async function fetchStats() {
    const { data } = await api.get('/dashboard/stats')
    stats.value = data
    return data
  }

  return {
    customers,
    deals,
    products,
    orders,
    stats,
    fetchCustomers,
    createCustomer,
    updateCustomer,
    deleteCustomer,
    fetchDeals,
    createDeal,
    updateDeal,
    deleteDeal,
    fetchProducts,
    createProduct,
    updateProduct,
    deleteProduct,
    fetchOrders,
    createOrder,
    updateOrderStatus,
    deleteOrder,
    fetchStats,
  }
})
