<script lang="ts">
  import {
    getImageViewerController,
    type ContextMenuItemType,
    type ContextMenuItem,
  } from "$lib/contexts/ol_image_viewer/controller.svelte";
  import { portal } from "$lib/actions/portal";

  interface Props {
    x: number;
    y: number;
    items: ContextMenuItem[];
  }

  let { x, y, items }: Props = $props();

  const imageViewer = getImageViewerController();

  let selected = $state<ContextMenuItem | null>(
    items.length === 1 ? items[0] : null,
  );

  const typePrefix: Record<ContextMenuItemType, string> = {
    equipment: "Equipment",
    ghost: "Ghost",
    measurement: "Measurement",
  };

  function handleBackdropClick(e: PointerEvent) {
    if (e.target === e.currentTarget) imageViewer.closeContextMenu();
  }
</script>

<svelte:window
  onkeydown={(e) => e.key === "Escape" && imageViewer.closeContextMenu()}
/>

<div {@attach portal()}>
  <menu class="context-menu" style="left: {x}px; top: {y}px">
    {#if selected === null}
      <!-- feature picker -->
      <li class="menu-header">Select feature</li>
      {#each items as item}
        <li>
          <button class="picker-row" onclick={() => (selected = item)}>
            {`${typePrefix[item.type]}: ${item.label}`}
          </button>
        </li>
      {/each}
    {:else}
      <!-- action picker -->
      <li class="menu-header">
        {`${typePrefix[selected.type]}: ${selected.label}`}
      </li>
      {#if selected.type === "equipment"}
        <li>
          <button
            onclick={() => {
              if (!selected) return;
              imageViewer.removeAnnotations([selected.feature]);
              imageViewer.closeContextMenu();
            }}>Delete</button
          >
        </li>
      {:else if selected.type === "ghost"}
        <li>
          <button
            onclick={() => {
              if (!selected) return;
              imageViewer.acceptGhosts([selected.feature]);
              imageViewer.closeContextMenu();
            }}
          >
            Accept
          </button>
        </li>
        <li>
          <button
            onclick={() => {
              if (!selected) return;
              imageViewer.removeGhosts([selected.feature]);
              imageViewer.closeContextMenu();
            }}
          >
            Hide
          </button>
        </li>
      {:else if selected.type === "measurement"}
        <li>
          <button
            onclick={() => {
              if (!selected) return;
              imageViewer.removeMeasurements([selected.feature]);
              imageViewer.closeContextMenu();
            }}>Remove</button
          >
        </li>
      {/if}
    {/if}
  </menu>
</div>

<style>
  .context-menu {
    position: absolute;
    width: max-content;
    height: max-content;
    min-width: min-content;
    max-width: 10%;
    min-height: min-content;
    max-height: 10%;
    overflow-wrap: break-word;
    overflow-y: auto;
    list-style: none;
    margin: 0;
    padding: var(--size-sm) var(--size-md);
    background-color: oklch(var(--color-primary));
    border-radius: var(--size-sm);
  }

  .menu-header {
    color: oklch(var(--color-text) / 0.5);
    font-size: var(--text-sm);
    border-bottom: 1px solid oklch(var(--color-secondary-accent));
  }

  li button {
    width: 100%;
    height: 100%;
    text-align: left;
    background: none;
    border: none;
    color: oklch(var(--color-text));
  }
  li:has(> button):hover {
    background-color: oklch(var(--color-secondary) / 0.1);
  }
</style>
