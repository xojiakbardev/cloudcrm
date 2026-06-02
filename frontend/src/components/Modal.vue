<script setup>
defineProps({
  title: String,
  open: Boolean,
})
const emit = defineEmits(['close'])
</script>

<template>
  <Transition name="modal">
    <div v-if="open" class="modal-overlay" @click.self="emit('close')">
      <div class="modal" role="dialog" aria-modal="true">
        <div class="modal-head">
          <h3>{{ title }}</h3>
          <button class="btn btn-ghost btn-sm" @click="emit('close')" aria-label="Close">✕</button>
        </div>
        <div class="modal-body">
          <slot />
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  backdrop-filter: blur(3px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-md);
  z-index: 50;
}
.modal {
  background: #fff;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  width: 100%;
  max-width: 480px;
  max-height: 90vh;
  overflow-y: auto;
}
.modal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-lg);
  border-bottom: 1px solid var(--color-border);
}
.modal-head h3 { font-size: 17px; }
.modal-body { padding: var(--space-lg); }
.modal-enter-active,
.modal-leave-active { transition: opacity 200ms ease; }
.modal-enter-from,
.modal-leave-to { opacity: 0; }
</style>
