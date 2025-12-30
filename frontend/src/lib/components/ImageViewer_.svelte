<script lang="ts">
  import { onDestroy } from "svelte";
  import Map from "ol/Map";
  import WebGLTileLayer, {
    type Style as RasterStyle,
  } from "ol/layer/WebGLTile";
  import VectorSource from "ol/source/Vector";
  import VectorLayer from "ol/layer/Vector";
  import { Draw, Modify, Select, Translate } from "ol/interaction";
  import { Circle, Fill, Stroke, Style, Text } from "ol/style";
  import Feature, { type FeatureLike } from "ol/Feature";
  import Collection from "ol/Collection";
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

  import type { ImageMetadata, RadiometricParams } from "$lib/utils/types";
  import {
    useImageViewer,
    type ImageViewerController,
  } from "$lib/hooks/useImageViewer";
  import { getAnnotateState } from "$lib/states/annotate.svelte";
  import frag from "$lib/shaders/slc_radiometric_correction_ol.frag.glsl?raw";

  interface Props {
    image: ImageMetadata | null;
    radiometricParams?: RadiometricParams | null;
    selectedFeatures: Feature[];
  }

  let {
    image = null,
    radiometricParams = null,
    selectedFeatures = $bindable(),
  }: Props = $props();

  const annotate = getAnnotateState();

  let map: Map | null = null;
  let controller: ImageViewerController | null = null;

  let drawInteraction: Draw | null = null;
  let hoverInteraction: Select | null = null;
  let selectInteraction: Select | null = null;
  let modifyInteraction: Modify | null = null;
  let translateInteraction: Translate | null = null;
  let equipmentSource: VectorSource | null = null;
  let activitySource: VectorSource | null = null;

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

  function textStyle(
    label: string,
    colorScheme: ColorScheme,
    alpha: number = 1.0,
    offsetY?: number | undefined,
  ) {
    return new Text({
      text: label,
      fill: new Fill({ color: colorScheme.fill(alpha) }),
      stroke: new Stroke({ color: colorScheme.stroke(alpha), width: 2 }),
      offsetY: offsetY,
    });
  }

  function featureStyle(
    feature: FeatureLike,
    colorScheme: ColorScheme,
    alpha: number = 1.0,
    polygonAlpha: number | undefined = 0.0,
    strokeWidth: number = 1.0,
  ) {
    const geometry = feature.getGeometry();
    if (!(geometry instanceof Geometry)) return null;

    const label = feature.get("label");

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
        text: label ? textStyle(label, textColor, 1.0, 25) : undefined,
      });
    }

    if (geometry instanceof Polygon || geometry instanceof MultiPolygon) {
      return new Style({
        stroke: new Stroke({
          color: colorScheme.fill(alpha),
          width: strokeWidth,
        }),
        fill:
          polygonAlpha === null
            ? undefined
            : new Fill({
                color: colorScheme.fill(polygonAlpha),
              }),
        text: label ? textStyle(label, textColor, 1.0, 10) : undefined,
      });
    }

    return null;
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

  function disableAllInteractions() {
    hoverInteraction?.setActive(false);
    selectInteraction?.setActive(false);
    modifyInteraction?.setActive(false);
    translateInteraction?.setActive(false);
    drawInteraction?.setActive(false);
  }

  function enterIdle() {
    disableAllInteractions();
  }

  function enterEdit() {
    disableAllInteractions();
    hoverInteraction?.setActive(true);
    selectInteraction?.setActive(true);
    modifyInteraction?.setActive(true);
    translateInteraction?.setActive(true);
  }

  function enterDraw() {
    if (!drawInteraction) return;

    disableAllInteractions();

    const source =
      annotate.layer === "equipment" ? equipmentSource! : activitySource!;
    drawInteraction!.setProperties({
      source,
      type: annotate.geometry,
    });
    drawInteraction.setActive(true);
  }

  function syncSelectedFeatures() {
    if (!selectInteraction) return;

    selectedFeatures = [...selectInteraction.getFeatures().getArray()];
  }

  function deleteFeature(feature: Feature) {
    const type = feature.get("type");
    const source = type === "equipment" ? equipmentSource : activitySource;
    if (!source) return;

    source.removeFeature(feature);
  }

  function setupInteractions(map: Map) {
    const modifiable = new Collection<Feature>();

    hoverInteraction = new Select({
      condition: pointerMove,
      hitTolerance: 5,
      filter: (feature) =>
        !selectInteraction?.getFeatures().getArray().includes(feature),
      style: (feature) => featureStyle(feature, equipmentColor, 1.0, 0.0, 2),
    });

    selectInteraction = new Select({
      addCondition: shiftKeyOnly,
      hitTolerance: 5,
      style: (feature) => {
        const features = selectInteraction!.getFeatures();
        const index = features.getArray().indexOf(feature);
        const base = featureStyle(feature, equipmentColor, 1.0, 0.2, 2);

        return index >= 0 && base
          ? [
              base,
              new Style({
                text: textStyle(`${index + 1}`, textColor, 1.0, -15),
              }),
              vertexStyle,
            ]
          : base;
      },
    });

    modifyInteraction = new Modify({ features: modifiable });

    translateInteraction = new Translate({
      condition: platformModifierKeyOnly,
      features: selectInteraction.getFeatures(),
    });

    drawInteraction = new Draw({
      source: equipmentSource!,
      type: "Point",
    });

    selectInteraction.getFeatures().on("add", (e) => {
      const g = e.element.getGeometry();
      if (g instanceof Polygon || g instanceof MultiPolygon) {
        modifiable.push(e.element);
      }
      syncSelectedFeatures();
    });

    selectInteraction.getFeatures().on("remove", (e) => {
      modifiable.remove(e.element);
      syncSelectedFeatures();
    });

    drawInteraction.on("drawend", (e) => {
      if (!annotate.validData) return;

      const label = annotate.label;

      e.feature.setProperties({
        type: annotate.layer,
        label,
        data: structuredClone($state.snapshot(annotate.data)),
      });
    });

    map.addInteraction(hoverInteraction);
    map.addInteraction(selectInteraction);
    map.addInteraction(modifyInteraction);
    map.addInteraction(translateInteraction);
    map.addInteraction(drawInteraction);

    enterIdle();
  }

  function attachMap(element: HTMLElement) {
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
        return featureStyle(feature, equipmentColor, 0.7, 0.0);
      },
    });

    activitySource = new VectorSource();
    const activityLayer = new VectorLayer({
      source: activitySource,
      style: (feature) => {
        return featureStyle(feature, activityColor, 0.7, 0.0);
      },
    });

    map = new Map({
      target: element,
      layers: [rasterLayer, equipmentLayer, activityLayer],
      view: rasterSource.getView(),
    });
    setupInteractions(map);
    controller = useImageViewer({
      enterIdle,
      enterEdit,
      enterDraw,
      deleteFeature,
    });
  }

  export function getController() {
    return controller;
  }

  // function cleanupInteractions() {
  // if (drawInteraction) {
  // map?.removeInteraction(drawInteraction);
  // drawInteraction = null;
  // }
  // if (hoverInteraction) {
  // map?.removeInteraction(hoverInteraction);
  // hoverInteraction = null;
  // }
  // if (selectInteraction) {
  // map?.removeInteraction(selectInteraction);
  // selectInteraction = null;
  // }
  // if (modifyInteraction) {
  // map?.removeInteraction(modifyInteraction);
  // modifyInteraction = null;
  // }
  // if (translateInteraction) {
  // map?.removeInteraction(translateInteraction);
  // translateInteraction = null;
  // }
  // }
  //
  // $effect(() => {
  // if (!map || !equipmentSource || !activitySource) return;
  //
  // cleanupInteractions();
  //
  // if (drawConfig.enabled) {
  // if (!formData) {
  // return;
  // }
  //
  // const drawSource =
  // drawConfig.layer === "equipment" ? equipmentSource : activitySource;
  //
  // drawInteraction = new Draw({
  // source: drawSource,
  // type: drawConfig.geometry,
  // });
  // drawInteraction.on("drawend", (event) => {
  // const feature = event.feature;
  //
  // const label =
  // drawConfig.layer === "equipment"
  // ? `${formData.id}\n${formData.status}\n${formData.confidence}`
  // : ""; //formData.activity
  //
  // feature.setProperties({
  // type: drawConfig.layer,
  // label,
  // data: structuredClone($state.snapshot(formData)),
  // });
  // });
  // map.addInteraction(drawInteraction);
  // } else {
  // const modifiableFeatures = new Collection<Feature>();
  //
  // hoverInteraction = new Select({
  // condition: pointerMove,
  // hitTolerance: 5,
  // filter: (feature) => {
  // return !selectInteraction?.getFeatures().getArray().includes(feature);
  // },
  // style: (feature) => {
  // return featureStyle(feature, equipmentColor, 1.0, 0.0, 2);
  // },
  // });
  // map.addInteraction(hoverInteraction);
  //
  // selectInteraction = new Select({
  // addCondition: shiftKeyOnly,
  // hitTolerance: 5,
  // style: (feature) => {
  // const features = selectInteraction!.getFeatures();
  // const index = features.getArray().indexOf(feature);
  //
  // const baseStyle = featureStyle(feature, equipmentColor, 1.0, 0.2, 2);
  //
  // if (!baseStyle || index < 0) return baseStyle;
  //
  // return [
  // baseStyle,
  // new Style({
  // text: textStyle(`${index + 1}`, textColor, 1.0, -15),
  // }),
  // vertexStyle,
  // ];
  // },
  // });
  // map.addInteraction(selectInteraction);
  // syncSelectedFeatures();
  //
  // selectInteraction.getFeatures().on("add", (e) => {
  // const geometry = e.element.getGeometry();
  //
  // if (geometry instanceof Polygon || geometry instanceof MultiPolygon) {
  // modifiableFeatures.push(e.element);
  // }
  //
  // syncSelectedFeatures();
  // });
  //
  // selectInteraction.getFeatures().on("remove", (e) => {
  // modifiableFeatures.remove(e.element);
  //
  // syncSelectedFeatures();
  // });
  //
  // modifyInteraction = new Modify({
  // features: modifiableFeatures,
  // });
  // map.addInteraction(modifyInteraction);
  //
  // translateInteraction = new Translate({
  // condition: platformModifierKeyOnly,
  // features: selectInteraction.getFeatures(),
  // });
  // map.addInteraction(translateInteraction);
  // }
  //
  // return cleanupInteractions;
  // });

  onDestroy(() => {
    map?.setTarget(undefined);
    map?.getLayers().clear();
  });
</script>

<div {@attach attachMap} class="map"></div>

<style>
  .map {
    width: 100%;
    height: 100%;
  }
</style>
