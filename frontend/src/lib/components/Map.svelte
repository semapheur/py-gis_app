<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import * as maplibre from "maplibre-gl";
  import "maplibre-gl/dist/maplibre-gl.css";

  export let extent: GeoJSON.Polygon | null = null;
  export let showSearchButton = false;
  export let onSearchExtent: (polygon: GeoJSON.Polygon) => void;

  let map: maplibre.Map;
  let mapContainer: HTMLDivElement;
  let resizeObserver: ResizeObserver;

  function getExtentGeoJSON(map: maplibre.Map): GeoJSON.Polygon {
    const bounds = map.getBounds();

    const west = bounds.getWest();
    const south = bounds.getSouth();
    const east = bounds.getEast();
    const north = bounds.getNorth();

    return {
      type: "Polygon",
      coordinates: [
        [
          [west, south],
          [east, south],
          [east, north],
          [west, north],
          [west, south],
        ],
      ],
    };
  }

  function searchCurrentExtent() {
    if (!(map && onSearchExtent)) return;

    const polygon = getExtentGeoJSON(map);
    onSearchExtent(polygon);
  }

  onMount(() => {
    //const initialState = { lng: 0.0, lat: 0.0, zoom: 10 };

    map = new maplibre.Map({
      container: mapContainer,
      style:
        "https://demotiles.maplibre.org/styles/osm-bright-gl-style/style.json",
    });
    map.addControl(new maplibre.NavigationControl(), "top-right");

    if (extent) {
      const coordinates = extent.coordinates[0];
      const lats = coordinates.map((c) => c[1]);
      const lngs = coordinates.map((c) => c[0]);
      const bounds = [
        [Math.min(...lngs), Math.min(...lats)],
        [Math.max(...lngs), Math.max(...lats)],
      ];
      map.fitBounds(bounds as maplibre.LngLatBoundsLike);
    }

    resizeObserver = new ResizeObserver(() => {
      if (map) map.resize();
    });
    resizeObserver.observe(mapContainer);

    onDestroy(() => {
      resizeObserver.disconnect();
      map.remove();
    });
  });
</script>

<div class="map" bind:this={mapContainer}>
  {#if showSearchButton}
    <button class="btn-search-extent" on:click={searchCurrentExtent}>
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
  .btn-search-extent {
    position: absolute;
    bottom: 1rem;
    left: 1rem;
    z-index: 1;
  }
</style>
