<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import Map from "ol/Map";
  import TileLayer from "ol/layer/WebGLTile.js";
  import GeoTIFF from "ol/source/GeoTIFF.js";
  import View from "ol/View";
  import { Projection } from "ol/proj";

  const epsg4326 = new Projection({
    code: "EPSG:4326",
    units: "degrees",
    axisOrientation: "enu",
  });

  //useGeographic();

  export let fileName: string | undefined;

  let map: Map | null = null;
  let target: HTMLDivElement;

  onMount(() => {
    if (fileName === undefined) return;

    const source = new GeoTIFF({
      sources: [
        {
          url: `http://localhost:8080/cog/${fileName}.cog.tif`,
          projection: epsg4326,
        },
      ],
    });

    const test = source.getView().then((viewConfig) => console.log(viewConfig));

    map = new Map({
      target,
      layers: [
        new TileLayer({
          source: source,
        }),
      ],
      view: source.getView(),
    });
  });

  onDestroy(() => {
    map?.setTarget(undefined);
  });
</script>

<div bind:this={target} class="map"></div>

<style>
  .map {
    width: 100%;
    height: 100%;
  }
</style>
