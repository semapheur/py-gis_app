<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import Map from "ol/Map";
  import WebGLTileLayer, { type Style } from "ol/layer/WebGLTile.js";
  import GeoTIFF from "ol/source/GeoTIFF.js";

  import type { ImageMetadata, RadiometricParams } from "$lib/utils/types";
  import frag from "$lib/shaders/slc_radiometric_correction.frag.glsl?raw";

  //useGeographic();

  export let image: ImageMetadata | null = null;
  export let radiometricParams: RadiometricParams | null = null;

  let map: Map | null = null;
  let target: HTMLDivElement;

  onMount(() => {
    if (!image) return;

    const source = new GeoTIFF({
      sources: [
        {
          url: `http://localhost:8080/cog/${image.filename}.cog.tif`,
        },
      ],
    });

    const style = radiometricParams
      ? ({
          fragmentShader: frag,
          uniforms: {
            u_noiseCoefs: radiometricParams.noise,
            u_sigmaZeroCoefs: radiometricParams.sigma0,
          },
        } as Style)
      : undefined;

    const layer = new WebGLTileLayer({
      source: source,
      style: style,
    });

    map = new Map({
      target,
      layers: [layer],
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
