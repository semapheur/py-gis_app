<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import Map from "ol/Map";
  import WebGLTileLayer, {
    type Style as RasterStyle,
  } from "ol/layer/WebGLTile.js";
  import VectorSource from "ol/source/Vector";
  import VectorLayer from "ol/layer/Vector";
  import { Draw, Modify, Translate } from "ol/interaction";
  import { Circle, Fill, Stroke, Style, Text } from "ol/style.js";
  import GeoTIFF from "ol/source/GeoTIFF.js";

  import type {
    ImageMetadata,
    RadiometricParams,
    AnnotateForm,
    AnnotateGeometry,
    EquipmentData,
  } from "$lib/utils/types";
  import frag from "$lib/shaders/slc_radiometric_correction_ol.frag.glsl?raw";

  interface Props {
    image: ImageMetadata | null;
    radiometricParams?: RadiometricParams | null;
    drawMode: boolean;
    drawLayer: AnnotateForm | null;
    drawGeometry: AnnotateGeometry<AnnotateForm> | null;
    formData: EquipmentData | null;
  }

  let {
    image = null,
    radiometricParams = null,
    drawMode = $bindable(false),
    drawLayer = $bindable(null),
    drawGeometry = $bindable(null),
    formData = null,
  }: Props = $props();

  let map: Map | null = null;
  let drawInteraction: Draw | null = null;
  let modifyInteraction: Modify | null = null;
  let translateInteraction: Translate | null = null;
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
        } as RasterStyle)
      : undefined;

    const rasterLayer = new WebGLTileLayer({
      source: rasterSource,
      style: rasterStyle,
    });

    equipmentSource = new VectorSource();
    const equipmentLayer = new VectorLayer({
      source: equipmentSource,
      style: (feature) => {
        const data = feature.get("data");

        const label = data
          ? `${data.id}\n${data.status}\n${data.confidence}`
          : "";

        return new Style({
          image: new Circle({
            radius: 5,
            fill: new Fill({ color: "red" }),
            stroke: new Stroke({ color: "#fff", width: 1 }),
          }),
          stroke: new Stroke({
            color: "red",
            width: 1,
          }),
          text: new Text({
            text: label,
            stroke: new Stroke({ color: "#fff", width: 1 }),
            offsetY: 25,
          }),
        });
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

  function cleanupInteractions() {
    if (drawInteraction) {
      map?.removeInteraction(drawInteraction);
      drawInteraction = null;
    }
    if (modifyInteraction) {
      map?.removeInteraction(modifyInteraction);
      modifyInteraction = null;
    }
    if (translateInteraction) {
      map?.removeInteraction(translateInteraction);
      translateInteraction = null;
    }
  }

  $effect(() => {
    if (!map) return;

    cleanupInteractions();

    if (
      !drawMode ||
      !drawLayer ||
      !drawGeometry ||
      !equipmentSource ||
      !activitySource ||
      !formData
    ) {
      return;
    }

    const interactionSource =
      drawLayer === "equipment" ? equipmentSource : activitySource;

    if (drawMode) {
      drawInteraction = new Draw({
        source: interactionSource,
        type: drawGeometry,
      });
      drawInteraction.on("drawend", (event) => {
        const feature = event.feature;

        feature.setProperties({
          data: structuredClone($state.snapshot(formData)),
        });
      });
      map.addInteraction(drawInteraction);
    } else {
      if (drawGeometry === "Polygon" || drawGeometry === "MultiPolygon") {
        modifyInteraction = new Modify({ source: interactionSource });
        map.addInteraction(modifyInteraction);
      }
      translateInteraction = new Translate({
        features: interactionSource.getFeaturesCollection(),
      });
      map.addInteraction(translateInteraction);
    }

    return cleanupInteractions;
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
