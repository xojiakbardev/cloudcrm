<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import Icon from '../components/Icon.vue'

const auth = useAuthStore()
const router = useRouter()

const nav = [
  { to: '/dashboard', label: 'Dashboard', icon: 'dashboard' },
  { to: '/customers', label: 'Customers', icon: 'users' },
  { to: '/deals', label: 'Deals', icon: 'deals' },
  { to: '/infrastructure', label: 'Infrastructure', icon: 'network' },
]

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark">
          <Icon name="activity" :size="20" />
        </div>
        <span>CloudCRM</span>
      </div>

      <nav class="nav">
        <router-link
          v-for="item in nav"
          :key="item.to"
          :to="item.to"
          class="nav-item"
          active-class="nav-item-active"
        >
          <Icon :name="item.icon" :size="18" />
          <span>{{ item.label }}</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <div class="user-info" v-if="auth.user">
          <div class="user-avatar">{{ auth.user.full_name.charAt(0) }}</div>
          <div class="user-meta">
            <div class="user-name">{{ auth.user.full_name }}</div>
            <div class="user-role">{{ auth.user.role }}</div>
          </div>
        </div>
        <button class="btn btn-ghost logout-btn" @click="logout">
          <Icon name="logout" :size="16" />
          <span>Logout</span>
        </button>
      </div>
    </aside>

    <main class="main">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.layout {
  display: flex;
  min-height: 100vh;
}
.sidebar {
  width: 248px;
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  padding: var(--space-lg) var(--space-md);
  position: sticky;
  top: 0;
  height: 100vh;
}
.brand {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 18px;
  font-weight: 700;
  padding: 0 var(--space-sm) var(--space-lg);
}
.brand-mark {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  background: var(--color-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
}
.nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: 10px 12px;
  border-radius: var(--radius-md);
  color: var(--color-muted-foreground);
  font-weight: 500;
  font-size: 14px;
  transition: background 150ms ease, color 150ms ease;
}
.nav-item:hover {
  background: var(--color-muted);
  color: var(--color-foreground);
}
.nav-item-active {
  background: var(--color-primary);
  color: #fff;
}
.sidebar-footer {
  border-top: 1px solid var(--color-border);
  padding-top: var(--space-md);
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}
.user-info {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: 0 var(--space-sm);
}
.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--color-secondary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
}
.user-name { font-size: 14px; font-weight: 600; }
.user-role { font-size: 12px; color: var(--color-muted-foreground); text-transform: capitalize; }
.logout-btn { justify-content: flex-start; width: 100%; }
.main {
  flex: 1;
  padding: var(--space-xl);
  max-width: 100%;
  overflow-x: hidden;
}
@media (max-width: 768px) {
  .layout { flex-direction: column; }
  .sidebar {
    width: 100%;
    height: auto;
    position: relative;
    flex-direction: row;
    flex-wrap: wrap;
    align-items: center;
  }
  .nav { flex-direction: row; flex-wrap: wrap; }
  .nav-item span { display: none; }
  .sidebar-footer { border-top: none; padding-top: 0; flex-direction: row; }
  .user-info { display: none; }
  .main { padding: var(--space-md); }
}
</style>
