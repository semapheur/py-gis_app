<script lang="ts">
  import type { Snippet } from "svelte";

  interface Props {
    open: boolean;
    children: Snippet;
  }

  let { open = $bindable(), children }: Props = $props();
  let dialog: HTMLDialogElement | null = null;

  $effect(() => {
    if (!dialog) return;

    if (open && !dialog.open) {
      dialog.showModal();
    } else if (!open && dialog.open) {
      dialog.close();
    }
  });
</script>

<dialog
  bind:this={dialog}
  onclose={() => (open = false)}
  oncancel={() => (open = false)}
>
  <header>
    <button class="button-close" type="button" onclick={() => (open = false)}>
      ✕
    </button>
  </header>
  {@render children()}
</dialog>

<style>
  dialog {
    display: grid;
    grid-template-rows: auto 1fr;

    &::backdrop {
      background: rbga(0 0 0 / 0.4);
    }
  }

  .button-close {
    all: unset;

    &:hover {
      color: red;
    }
  }
</style>
