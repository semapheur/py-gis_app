<script lang="ts">
  import { getAreaEditorState } from "$lib/contexts/area_editor.svelte";
  import { getAreaMapState } from "$lib/contexts/ol_area_map.svelte";

  const map = getAreaMapState();
  const editor = getAreaEditorState();

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
  <div class="layer-select">
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
  </div>
</div>

<style>
  .map {
    position: relative;
  }

  .layer-select {
    position: absolute;
    bottom: 1rem;
    left: 1rem;
    z-index: 1;
    display: flex;
    flex-direction: column;
    gap: var(--size-sm);
    background-color: oklch(var(--color-primary));
    padding: var(--size-sm);
    border-radius: var(--size-sm);
  }
</style>
