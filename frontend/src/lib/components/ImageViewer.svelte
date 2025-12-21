<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import Map from "ol/Map";
  import WebGLTileLayer, { type Style } from "ol/layer/WebGLTile.js";
  import VectorSource from "ol/source/Vector";
  import VectorLayer from "ol/layer/Vector";
  import { Draw } from "ol/interaction";
  import GeoTIFF from "ol/source/GeoTIFF.js";

  import type { ImageMetadata, RadiometricParams } from "$lib/utils/types";
  import frag from "$lib/shaders/slc_radiometric_correction_ol.frag.glsl?raw";

  //useGeographic();

  export let image: ImageMetadata | null = null;
  export let radiometricParams: RadiometricParams | null = null;
  export let drawEquipmentGeometry: "Polygon" | "Point" | null = null;

  let map: Map | null = null;
  let target: HTMLDivElement;

  onMount(() => {
    if (!image) return;

    const rasterSource = new GeoTIFF({
      sources: [
        {
          url: "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/36/Q/WD/2020/7/S2A_36QWD_20200701_0_L2A/TCI.tif", //`http://localhost:8080/cog/${image.filename}.cog.tif`,
        },
      ],
    });
    const rasterStyle = radiometricParams
      ? ({
          fragmentShader: frag,
          uniforms: {
            u_noiseCoefs: radiometricParams.noise.poly.flat(),
            u_sigmaZeroCoefs: radiometricParams.sigma0.flat(),
          },
        } as Style)
      : undefined;

    const rasterLayer = new WebGLTileLayer({
      source: rasterSource,
      style: rasterStyle,
    });

    const equipmentSource = new VectorSource();
    const equipmentLayer = new VectorLayer({
      source: equipmentSource,
      style: {
        "stroke-color": "red",
        "stroke-width": 2,
      },
    });

    map = new Map({
      target,
      layers: [rasterLayer, equipmentLayer],
      view: rasterSource.getView(),
    });

    if (drawEquipmentGeometry) {
      const draw = new Draw({
        source: equipmentSource,
        type: drawEquipmentGeometry, // change to 'Point' to draw points
      });
      map.addInteraction(draw);
    }
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
