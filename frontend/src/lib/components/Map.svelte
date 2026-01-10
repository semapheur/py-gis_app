<script lang="ts">
  import "maplibre-gl/dist/maplibre-gl.css";
  import { type ImagePreviewInfo } from "$lib/utils/types";
  import { getMapLibreState } from "$lib/contexts/maplibre.svelte";

  interface Props {
    extent?: GeoJSON.Polygon | null;
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

  const mapLibre = getMapLibreState();

  function searchCurrentExtent() {
    if (!mapLibre || !onSearchExtent) return;
    onSearchExtent(mapLibre.getCurrentExtentWkt());
  }

  $effect(() => {
    if (!mapLibre || !imagePreview) return;
    mapLibre.setImagePreview(imagePreview);
  });

  $effect(() => {
    if (!mapLibre || !extent) return;
    mapLibre.setInitialExtent(extent);
  });
</script>

<div class="map" {@attach (el) => mapLibre.attach(el)}>
  {#if showSearchButton}
    <button class="search-extent" onclick={searchCurrentExtent}>
      Search extent
    </button>
  {/if}
</div>

<style>
  .map {
    position: relative;
    width: 100%;
    height: 100%;
  }
  .search-extent {
    position: absolute;
    bottom: 1rem;
    left: 1rem;
    z-index: 1;
  }
</style>
