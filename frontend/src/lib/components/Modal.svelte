<script lang="ts">
  import type { Snippet } from "svelte";
  import CloseButton from "$lib/components/CloseButton.svelte";

  interface Props {
    open: boolean;
    children: Snippet;
  }

  let { open = $bindable(), children }: Props = $props();
  let dialog: HTMLDialogElement | null = null;

  function _onclick(e: MouseEvent & { currentTarget: HTMLDialogElement }) {
    if (e.target !== e.currentTarget) return;

    const rect = e.currentTarget.getBoundingClientRect();

    const clickedOutside =
      e.clientX < rect.left ||
      e.clientX > rect.right ||
      e.clientY < rect.top ||
      e.clientY > rect.bottom;

    if (clickedOutside) {
      open = false;
    }
  }

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
  onclick={_onclick}
  onclose={() => (open = false)}
  oncancel={() => (open = false)}
>
  <header>
    <CloseButton onclick={() => (open = false)} />
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
</style>
