<script lang="ts">
  import { toast } from "$lib/stores/toast.svelte";
</script>

<div class="toast-container">
  {#each toast.items as t (t.id)}
    <div class="toast {t.type}" role="alert">
      <span>{t.message}</span>
      <button onclick={() => toast.remove(t.id)}>✕</button>
    </div>
  {/each}
</div>

<style>
  .toast-container {
    position: fixed;
    top: var(--size-md);
    right: var(--size-md);
    display: flex;
    flex-direction: column;
    gap: var(--size-md);
    z-index: 2;
  }

  .toast {
    display: flex;
    justify-content: space-between;
    gap: var(--size-md);
  }

  .success {
    background: #22c55e;
  }
  .error {
    background: #ef4444;
  }
  .warning {
    background: #f59e0b;
  }
  .info {
    background: #3b82f6;
  }
</style>
