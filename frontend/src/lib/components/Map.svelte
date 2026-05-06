<script lang="ts">
  import { browser } from "$app/environment";
  import { goto } from "$app/navigation";
  import { page } from "$app/state";
  import "maplibre-gl/dist/maplibre-gl.css";
  import { type ImagePreviewInfo } from "$lib/utils/types";
  import { getMapLibreState } from "$lib/contexts/ml_map.svelte";
  import Button from "$lib/components/Button.svelte";
  import MdiLayersOutline from "@iconify-svelte/mdi/layers-outline";
  import { parseBbox } from "$lib/utils/geo/bbox";

  interface Props {
    imagePreview?: ImagePreviewInfo | null;
    extentPolygon?: GeoJSON.Polygon | null;
    showSearchButton?: boolean;
    syncBbox?: boolean;
    onSearchExtent?: (polygonWkt: string) => void;
  }

  let {
    imagePreview = null,
    extentPolygon = null,
    showSearchButton = false,
    syncBbox = false,
    onSearchExtent,
  }: Props = $props();

  let showLayers = $state<boolean>(false);
  const initialBbox = $derived(
    syncBbox && browser ? page.url.searchParams.get("bbox") : null,
  );
  const mapLibre = getMapLibreState();

  function searchCurrentExtent() {
    if (!mapLibre || !onSearchExtent) return;

    const extentWkt = mapLibre.getCurrentExtentWkt();
    if (!extentWkt) return;

    onSearchExtent(extentWkt);
  }

  $effect(() => {
    if (!syncBbox || !browser) return;

    const cleanup = mapLibre.onMoveEnd((bbox) => {
      const params = new URLSearchParams(page.url.searchParams);
      params.set("bbox", bbox);
      goto(`?${params}`, {
        replaceState: true,
        keepFocus: true,
        noScroll: true,
      });
    });

    return cleanup;
  });

  $effect(() => {
    if (!mapLibre || !initialBbox) return;

    const bbox = parseBbox(initialBbox);

    mapLibre.setInitialExtent(bbox);
  });

  $effect(() => {
    if (!mapLibre || !extentPolygon) return;
    mapLibre.zoomToPolygon("search-extent", extentPolygon, { animate: false });
  });

  $effect(() => {
    if (!mapLibre || !imagePreview) return;
    mapLibre.setImagePreview(imagePreview);
  });
</script>

<div class="map" {@attach (el) => mapLibre.attach(el)}>
  {#if showSearchButton}
    <div class="map-button">
      <Button onclick={searchCurrentExtent}>Search extent</Button>
    </div>
  {/if}

  <div
    class="layer-control"
    role="group"
    onmouseenter={() => (showLayers = true)}
    onmouseleave={() => (showLayers = false)}
  >
    {#if showLayers}
      {#each mapLibre.layers as layer}
        <label>
          <input
            type="radio"
            name="map-layer"
            value={layer.id}
            checked={layer.visible}
            onchange={() => mapLibre.selectLayer(layer.id)}
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
    width: 100%;
    height: 100%;
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

  .map-button {
    position: absolute;
    bottom: var(--size-lg);
    left: var(--size-lg);
    z-index: 1;
  }
</style>
