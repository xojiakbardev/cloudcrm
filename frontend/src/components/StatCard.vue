<script setup>
import Icon from './Icon.vue'

defineProps({
  label: String,
  value: [String, Number],
  icon: String,
  accent: { type: String, default: 'blue' },
})
</script>

<template>
  <div class="stat-card">
    <div :class="['stat-icon', `stat-icon-${accent}`]">
      <Icon :name="icon" :size="22" />
    </div>
    <div>
      <div class="stat-value">{{ value }}</div>
      <div class="stat-label">{{ label }}</div>
    </div>
  </div>
</template>

<style scoped>
.stat-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
  display: flex;
  align-items: center;
  gap: var(--space-md);
  box-shadow: var(--shadow-sm);
  transition: box-shadow 200ms ease, transform 200ms ease;
}
.stat-card:hover {
  box-shadow: var(--shadow-md);
}
.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.stat-icon-blue { background: #dbeafe; color: #1d4ed8; }
.stat-icon-green { background: #dcfce7; color: #047857; }
.stat-icon-amber { background: #fef3c7; color: #b45309; }
.stat-icon-gray { background: #f1f5f9; color: #475569; }
.stat-value {
  font-size: 26px;
  font-weight: 700;
  font-family: var(--font-mono);
  line-height: 1.1;
}
.stat-label {
  font-size: 13px;
  color: var(--color-muted-foreground);
  margin-top: 2px;
}
</style>
