<script lang="ts">
  import type { Snippet } from "svelte";
  import CloseButton from "$lib/components/CloseButton.svelte";

  interface Props {
    open: boolean;
    children: Snippet;
  }

  let { open = $bindable(), children }: Props = $props();
  let dialog = $state<HTMLDialogElement | null>(null);

  $effect(() => {
    if (!dialog) return;

    if (open) {
      dialog.showModal();
    } else {
      dialog.close();
    }
  });
</script>

{#if open}
  <dialog
    bind:this={dialog}
    onclick={(e) => {
      if (e.target === dialog) dialog?.close();
    }}
    onclose={() => (open = false)}
  >
    <header>
      <CloseButton onclick={() => dialog?.close()} />
    </header>
    {@render children()}
  </dialog>
{/if}

<style>
  dialog {
    display: grid;
    grid-template-rows: auto 1fr;

    &::backdrop {
      background: rbga(0 0 0 / 0.4);
    }
  }
</style>
