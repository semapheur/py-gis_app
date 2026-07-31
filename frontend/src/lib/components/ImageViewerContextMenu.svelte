<script lang="ts">
  import { page } from "$app/state";
  import {
    getImageViewerController,
    type ContextMenuFeatureType,
    type ContextMenuItem,
  } from "$lib/contexts/ol_image_viewer/controller.svelte";
  import { portal } from "$lib/actions/portal";
  import { toast } from "$lib/stores/toast.svelte";

  interface Props {
    x: number;
    y: number;
    items: ContextMenuItem[];
  }

  let { x, y, items }: Props = $props();
  const imageViewer = getImageViewerController();

  let manualSelection = $state<ContextMenuItem | null>(null);
  let selected = $derived(
    manualSelection ?? (items.length === 1 ? items[0] : null),
  );

  $effect(() => {
    items;
    manualSelection = null;
  });

  const typePrefix: Record<ContextMenuFeatureType, string> = {
    equipment: "Equipment",
    ghost: "Ghost",
    measurement: "Measurement",
  };

  function itemLabel(item: ContextMenuItem) {
    if (item.type === "coordinate") {
      return `DMS: ${item.dms}\nMGRS: ${item.mgrs}`;
    }

    if (item.features.length > 1) {
      return item.label;
    }

    return `${typePrefix[item.type]}: ${item.label}`;
  }

  async function copyToClipboard(text: string) {
    try {
      await navigator.clipboard.writeText(text);
      toast.success("Copied to clipboard");
    } catch (error) {
      console.error("Failed to copy:", error);
      toast.error("Failed to copy");
    }
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
          <button class="picker-row" onclick={() => (manualSelection = item)}>
            {itemLabel(item)}
          </button>
        </li>
      {/each}
    {:else}
      <!-- action picker -->
      <li class="menu-header">{itemLabel(selected)}</li>
      {#if selected.type === "equipment"}
        <li>
          <button
            onclick={() => {
              if (!selected || selected.type !== "equipment") return;
              imageViewer.removeAnnotations(selected.features);
              imageViewer.closeContextMenu();
            }}>Delete</button
          >
        </li>
      {:else if selected.type === "ghost"}
        <li>
          <button
            onclick={() => {
              if (!selected || selected.type !== "ghost") return;
              imageViewer.acceptGhosts(selected.features);
              imageViewer.closeContextMenu();
            }}
          >
            Accept
          </button>
        </li>
        <li>
          <button
            onclick={() => {
              if (!selected || selected.type !== "ghost") return;
              imageViewer.removeGhosts(selected.features);
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
              if (!selected || selected.type !== "measurement") return;
              imageViewer.removeMeasurements(selected.features);
              imageViewer.closeContextMenu();
            }}>Remove</button
          >
        </li>
      {:else if selected.type === "coordinate"}
        <li>
          <button
            onclick={() => {
              if (!selected || selected.type !== "coordinate") return;
              copyToClipboard(selected.dms);
              imageViewer.closeContextMenu();
            }}>Copy DMS</button
          >
          <button
            onclick={() => {
              if (!selected || selected.type !== "coordinate") return;
              copyToClipboard(selected.mgrs);
              imageViewer.closeContextMenu();
            }}>Copy MGRS</button
          >
          <button
            onclick={() => {
              if (!selected || selected.type !== "coordinate") return;
              const link = `${page.url.host}${page.url.pathname}?wkt=${selected.wkt}`;
              copyToClipboard(link);
              imageViewer.closeContextMenu();
            }}>Copy link</button
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
