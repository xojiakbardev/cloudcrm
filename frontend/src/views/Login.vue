<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import Icon from '../components/Icon.vue'

const auth = useAuthStore()
const router = useRouter()

const email = ref('admin@cloudcrm.dev')
const password = ref('admin123')
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(email.value, password.value)
    router.push('/dashboard')
  } catch (e) {
    error.value = e.response?.data?.detail || "Kirib bo'lmadi. Login ma'lumotlarini tekshiring."
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-wrap">
    <div class="login-card card">
      <div class="login-head">
        <div class="brand-mark">
          <Icon name="activity" :size="22" />
        </div>
        <h1>CloudCRM</h1>
        <p class="text-muted">Tizimga kiring</p>
      </div>

      <form @submit.prevent="submit">
        <div class="form-group">
          <label class="field-label" for="email">Email</label>
          <input id="email" class="input" type="email" v-model="email" required />
        </div>
        <div class="form-group">
          <label class="field-label" for="password">Parol</label>
          <input id="password" class="input" type="password" v-model="password" required />
        </div>

        <p v-if="error" class="error">{{ error }}</p>

        <button class="btn btn-primary login-btn" type="submit" :disabled="loading">
          {{ loading ? "Kirilmoqda..." : 'Kirish' }}
        </button>
      </form>

      <p class="demo-hint text-muted">
        Demo: <span class="mono">admin@cloudcrm.dev</span> / <span class="mono">admin123</span>
      </p>
    </div>
  </div>
</template>

<style scoped>
.login-wrap {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-md);
  background: linear-gradient(135deg, #eff6ff 0%, #f8fafc 100%);
}
.login-card {
  width: 100%;
  max-width: 400px;
  box-shadow: var(--shadow-lg);
}
.login-head {
  text-align: center;
  margin-bottom: var(--space-xl);
}
.brand-mark {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
  background: var(--color-primary);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-bottom: var(--space-md);
}
.login-head h1 { font-size: 24px; }
.form-group { margin-bottom: var(--space-md); }
.login-btn { width: 100%; margin-top: var(--space-sm); }
.error {
  color: var(--color-destructive);
  font-size: 14px;
  margin-bottom: var(--space-sm);
}
.demo-hint {
  text-align: center;
  font-size: 13px;
  margin-top: var(--space-lg);
}
</style>
