<script lang="ts">
  import type { Snippet } from "svelte";
  import CloseButton from "$lib/components/CloseButton.svelte";

  interface Props {
    open: boolean;
    title?: string;
    children: Snippet;
  }

  let { open = $bindable(), title, children }: Props = $props();
  let dialog = $state<HTMLDialogElement | null>(null);

  let pos = $state<{ x: number; y: number } | null>(null);
  let dragging = $state<boolean>(false);
  let dragStart = { x: 0, y: 0, offsetX: 0, offsetY: 0 };

  $effect(() => {
    if (!dialog) return;

    if (open) {
      dialog.showModal();
    } else {
      dialog.close();
    }
  });

  function onDragStart(e: PointerEvent) {
    if (!dialog) return;

    const rect = dialog.getBoundingClientRect();
    if (pos === null) {
      pos = { x: rect.left, y: rect.top };
    }
    dragStart = { x: e.clientX, y: e.clientY, offsetX: pos.x, offsetY: pos.y };
    dragging = true;
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
  }

  function onDragMove(e: PointerEvent) {
    if (!dragging || !dialog) return;
    const dx = e.clientX - dragStart.x;
    const dy = e.clientY - dragStart.y;

    let x = dragStart.offsetX + dx;
    let y = dragStart.offsetY + dy;

    const rect = dialog.getBoundingClientRect();
    const maxX = window.innerWidth - rect.width;
    const maxY = window.innerHeight - rect.height;
    x = Math.min(Math.max(0, x), Math.max(0, maxX));
    y = Math.min(Math.max(0, y), Math.max(0, maxY));

    pos = { x, y };
  }

  function onDragEnd(e: PointerEvent) {
    dragging = false;
    (e.target as HTMLElement).releasePointerCapture(e.pointerId);
  }

  $effect(() => {
    if (open) pos = null;
  });
</script>

{#if open}
  <dialog
    bind:this={dialog}
    style={pos ? `margin: 0; left: ${pos.x}px; top: ${pos.y}px;` : ""}
    onclick={(e) => {
      if (e.target === dialog) dialog?.close();
    }}
    onclose={() => (open = false)}
  >
    <header
      onpointerdown={onDragStart}
      onpointermove={onDragMove}
      onpointerup={onDragEnd}
      role="heading"
    >
      <span>{title}</span>
      <CloseButton onclick={() => dialog?.close()} />
    </header>
    {@render children()}
  </dialog>
{/if}

<style>
  dialog {
    display: grid;
    grid-template-rows: auto 1fr;
    background-color: oklch(var(--color-primary));

    &::backdrop {
      background: rgba(0 0 0 / 0.4);
    }
  }

  header {
    display: flex;
    justify-content: space-between;
    gap: var(--size-md);
    cursor: move;
    touch-action: none;
    user-select: none;
  }

  span {
    color: oklch(var(--color-text));
  }
</style>
