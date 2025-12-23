<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import Map from "ol/Map";
  import WebGLTileLayer, {
    type Style as RasterStyle,
  } from "ol/layer/WebGLTile";
  import VectorSource from "ol/source/Vector";
  import VectorLayer from "ol/layer/Vector";
  import { Draw, Modify, Select, Translate } from "ol/interaction";
  import { Circle, Fill, Stroke, Style, Text } from "ol/style";
  import type { FeatureLike } from "ol/Feature";
  import Geometry from "ol/geom/Geometry";
  import Point from "ol/geom/Point";
  import MultiPoint from "ol/geom/MultiPoint";
  import Polygon from "ol/geom/Polygon";
  import MultiPolygon from "ol/geom/MultiPolygon";
  import {
    platformModifierKeyOnly,
    pointerMove,
    shiftKeyOnly,
  } from "ol/events/condition";
  import GeoTIFF from "ol/source/GeoTIFF";

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
  let hoverInteraction: Select | null = null;
  let selectInteraction: Select | null = null;
  let modifyInteraction: Modify | null = null;
  let translateInteraction: Translate | null = null;
  let equipmentSource: VectorSource | null = null;
  let activitySource: VectorSource | null = null;
  let target: HTMLDivElement;

  interface ColorScheme {
    fill: (alpha?: number) => string;
    stroke: (alpha?: number) => string;
  }

  const textColor = {
    fill: (alpha: number = 1.0) => `rgba(250,250,249,${alpha})`,
    stroke: (alpha: number = 1.0) => `rgba(28,25,23,${alpha})`,
  };
  const equipmentColor = {
    fill: (alpha: number = 1.0) => `rgba(255,0,0,${alpha})`,
    stroke: (alpha: number = 1.0) => `rgba(255,255,255,${alpha})`,
  };
  const activityColor = {
    fill: (alpha: number = 1.0) => `rgba(0,255,0,${alpha})`,
    stroke: (alpha: number = 1.0) => `rgba(255,255,255,${alpha})`,
  };
  function geometryStyle(
    geometry: Geometry,
    label: string,
    colorScheme: ColorScheme,
    alpha: number = 1.0,
    strokeWidth: number = 1.0,
  ) {
    if (geometry instanceof Point) {
      return new Style({
        image: new Circle({
          radius: 5,
          fill: new Fill({ color: colorScheme.fill(alpha) }),
          stroke: new Stroke({
            color: equipmentColor.stroke(alpha),
            width: strokeWidth,
          }),
        }),
        text: new Text({
          text: label,
          fill: new Fill({ color: textColor.fill() }),
          stroke: new Stroke({ color: textColor.stroke(), width: 1 }),
          offsetY: 25,
        }),
      });
    }

    if (geometry instanceof Polygon || geometry instanceof MultiPolygon) {
      return new Style({
        stroke: new Stroke({
          color: colorScheme.fill(alpha),
          width: strokeWidth,
        }),
        fill: new Fill({
          color: colorScheme.fill(0.0),
        }),
        text: new Text({
          text: label,
          fill: new Fill({ color: textColor.fill() }),
          stroke: new Stroke({ color: textColor.stroke(), width: 1 }),
        }),
      });
    }
  }

  const vertexStyle = new Style({
    image: new Circle({
      radius: 3,
      fill: new Fill({ color: "#fff" }),
      stroke: new Stroke({ color: "#000", width: 1 }),
    }),
    geometry: (feature) => {
      const geometry = feature.getGeometry();
      if (geometry instanceof Polygon) {
        return new MultiPoint(geometry.getCoordinates()[0]);
      }

      if (geometry instanceof MultiPolygon) {
        return new MultiPoint(geometry.getCoordinates().flatMap((p) => p[0]));
      }
    },
  });

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
        const geometry = feature.getGeometry();
        if (!(geometry instanceof Geometry)) return;

        const data = feature.get("data");

        const label = data
          ? `${data.id}\n${data.status}\n${data.confidence}`
          : "";

        geometryStyle(geometry, label, equipmentColor, 0.7);
      },
    });

    activitySource = new VectorSource();
    const activityLayer = new VectorLayer({
      source: activitySource,
      style: (feature) => {
        const geometry = feature.getGeometry();
        if (!(geometry instanceof Geometry)) return;

        const data = feature.get("data");

        const label = data ? `${data.activity}` : "";

        geometryStyle(geometry, activityColor, 0.7, label);
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
    if (hoverInteraction) {
      map?.removeInteraction(hoverInteraction);
      hoverInteraction = null;
    }
    if (selectInteraction) {
      map?.removeInteraction(selectInteraction);
      selectInteraction = null;
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
    if (!map || !equipmentSource || !activitySource) return;

    cleanupInteractions();

    if (drawMode) {
      if (!drawLayer || !drawGeometry || !formData) {
        return;
      }

      const drawSource =
        drawLayer === "equipment" ? equipmentSource : activitySource;

      drawInteraction = new Draw({
        source: drawSource,
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
      selectInteraction = new Select({
        addCondition: shiftKeyOnly,
        hitTolerance: 5,
      });
      map.addInteraction(selectInteraction);

      modifyInteraction = new Modify({
        features: selectInteraction.getFeatures(),
      });
      map.addInteraction(modifyInteraction);

      translateInteraction = new Translate({
        condition: platformModifierKeyOnly,
        features: selectInteraction.getFeatures(),
      });
      map.addInteraction(translateInteraction);

      //const polygonFeatures = new Collection([
      //  ...activitySource.getFeatures(),
      //  ...equipmentSource.getFeatures().filter((feature) => {
      //    const geometry = feature.getGeometry();
      //    return (
      //      geometry?.getType() === "Polygon" ||
      //      geometry?.getType() === "MultiPolygon"
      //    );
      //  }),
      //]);
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
