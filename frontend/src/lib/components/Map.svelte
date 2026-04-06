<script lang="ts">
  import { goto } from "$app/navigation";
  import { page } from "$app/state";
  import "maplibre-gl/dist/maplibre-gl.css";
  import { type ImagePreviewInfo } from "$lib/utils/types";
  import { getMapLibreState } from "$lib/contexts/ml_map.svelte";
  import Button from "$lib/components/Button.svelte";
  import { parseBbox, type BBox } from "$lib/utils/geo/bbox";

  interface Props {
    extent?: BBox | null;
    imagePreview?: ImagePreviewInfo | null;
    showSearchButton?: boolean;
    onSearchExtent?: (polygonWkt: string) => void;
  }

  let {
    extent = null,
    imagePreview = null,
    showSearchButton = false,
    onSearchExtent,
  }: Props = $props();

  const initialBbox = page.url.searchParams.get("bbox");
  const mapLibre = getMapLibreState();

  function searchCurrentExtent() {
    if (!mapLibre || !onSearchExtent) return;
    onSearchExtent(mapLibre.getCurrentExtentWkt());
  }

  $effect(() => {
    if (!mapLibre) return;

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
    if (!mapLibre || !imagePreview) return;
    mapLibre.setImagePreview(imagePreview);
  });

  $effect(() => {
    if (!mapLibre || !extent) return;
    mapLibre.setInitialExtent(extent);
  });

  $effect(() => {
    if (!mapLibre || extent) return;
    if (!initialBbox) return;

    const bbox = parseBbox(initialBbox);

    mapLibre.setInitialExtent(bbox);
  });
</script>

<div class="map" {@attach (el) => mapLibre.attach(el)}>
  {#if showSearchButton}
    <div class="map-button">
      <Button onclick={searchCurrentExtent}>Search extent</Button>
    </div>
  {/if}
</div>

<style>
  .map {
    position: relative;
    width: 100%;
    height: 100%;
  }

  .map-button {
    position: absolute;
    bottom: 1rem;
    left: 1rem;
    z-index: 1;
  }
</style>
