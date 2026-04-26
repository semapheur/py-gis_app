<script lang="ts">
  import { toast } from "$lib/stores/toast.svelte";
  import MdiCancelCircleOutline from "@iconify-svelte/mdi/cancel-circle-outline";
  import ButtonIcon from "./ButtonIcon.svelte";
</script>

<div class="toaster">
  {#each toast.items as t (t.id)}
    <div class="toast {t.type}" role="alert">
      <span>{t.message}</span>
      <ButtonIcon onclick={() => toast.remove(t.id)}
        ><MdiCancelCircleOutline width="1rem" /></ButtonIcon
      >
    </div>
  {/each}
</div>

<style>
  .toaster {
    position: fixed;
    top: var(--size-md);
    right: var(--size-md);
    display: flex;
    flex-direction: column;
    gap: var(--size-md);
    z-index: 4;
  }

  .toast {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: var(--size-md);
    width: max-content;
    max-width: 20vw;
    padding: 0 var(--size-md);
    border-radius: var(--size-sm);
    backdrop-filter: blur(var(--blur-sm));
  }

  .success {
    background: oklch(72.3% 0.219 149.579/0.75);
  }
  .error {
    background: oklch(63.7% 0.237 25.331/0.75);
  }
  .warning {
    background: oklch(76.9% 0.188 70.08/0.75);
  }
  .info {
    background: oklch(68.5% 0.169 237.323/0.75);
  }
</style>
