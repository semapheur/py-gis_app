<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import Map from "ol/Map";
  import WebGLTileLayer, { type Style } from "ol/layer/WebGLTile.js";
  import VectorSource from "ol/source/Vector";
  import VectorLayer from "ol/layer/Vector";
  import { Draw } from "ol/interaction";
  import GeoTIFF from "ol/source/GeoTIFF.js";

  import type {
    ImageMetadata,
    RadiometricParams,
    AnnotateForm,
    AnnotateGeometry,
  } from "$lib/utils/types";
  import frag from "$lib/shaders/slc_radiometric_correction_ol.frag.glsl?raw";

  //useGeographic();

  interface Props {
    image: ImageMetadata | null;
    radiometricParams?: RadiometricParams | null;
    drawMode: boolean;
    drawLayer: AnnotateForm | null;
    drawGeometry: AnnotateGeometry<AnnotateForm> | null;
  }

  let {
    image = null,
    radiometricParams = null,
    drawMode = $bindable(false),
    drawLayer = $bindable(null),
    drawGeometry = $bindable(null),
  }: Props = $props();

  let map: Map | null = null;
  let drawInteraction: Draw | null = null;
  let equipmentSource: VectorSource | null = null;
  let activitySource: VectorSource | null = null;
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

    equipmentSource = new VectorSource();
    const equipmentLayer = new VectorLayer({
      source: equipmentSource,
      style: {
        "stroke-color": "red",
        "stroke-width": 1,
        "circle-radius": 5,
        "circle-fill-color": "red",
      },
    });

    activitySource = new VectorSource();
    const activityLayer = new VectorLayer({
      source: activitySource,
      style: {
        "stroke-color": "green",
        "stroke-width": 2,
      },
    });

    map = new Map({
      target,
      layers: [rasterLayer, equipmentLayer, activityLayer],
      view: rasterSource.getView(),
    });
  });

  $effect(() => {
    if (!map) return;

    if (drawInteraction) {
      map.removeInteraction(drawInteraction);
      drawInteraction = null;
    }

    if (
      !drawMode ||
      !drawLayer ||
      !drawGeometry ||
      !equipmentSource ||
      !activitySource
    ) {
      return;
    }

    drawInteraction = new Draw({
      source: drawLayer === "equipment" ? equipmentSource : activitySource,
      type: drawGeometry,
    });

    map.addInteraction(drawInteraction);

    return () => {
      if (drawInteraction) {
        map?.removeInteraction(drawInteraction);
        drawInteraction = null;
      }
    };
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
