<script lang="ts">
  import MdiLayersOutline from "@iconify-svelte/mdi/layers-outline";
  import { getAreaEditorState } from "$lib/contexts/area_editor.svelte";
  import { getAreaMapState } from "$lib/contexts/ol_area_map.svelte";

  const map = getAreaMapState();
  const editor = getAreaEditorState();

  let showLayers = $state<boolean>(false);

  $effect(() => {
    map.updateDrawInteraction(editor);
  });
</script>

<div
  class="map"
  {@attach (el) => {
    map.attach(el);
  }}
>
  <div
    class="layer-control"
    role="group"
    onmouseenter={() => (showLayers = true)}
    onmouseleave={() => (showLayers = false)}
  >
    {#if showLayers}
      {#each map.layers as layer}
        <label>
          <input
            type="radio"
            name="map-layer"
            value={layer.id}
            checked={layer.visible}
            onchange={() => map.selectLayer(layer.id)}
          />
          {layer.label}
        </label>
      {/each}
    {:else}
      <MdiLayersOutline width="1.5rem" />
    {/if}
  </div>
</div>

<style>
  .map {
    position: relative;
  }

  .layer-control {
    position: absolute;
    top: var(--size-lg);
    right: var(--size-lg);
    z-index: 1;
    display: flex;
    flex-direction: column;
    gap: var(--size-sm);
    background-color: oklch(var(--color-primary));
    padding: var(--size-sm);
    border-radius: var(--size-sm);
  }
</style>
