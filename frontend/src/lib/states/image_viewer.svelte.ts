import { getContext, setContext, untrack } from "svelte";
import Map from "ol/Map";
import WebGLTileLayer, { type Style as RasterStyle } from "ol/layer/WebGLTile";
import VectorLayer from "ol/layer/Vector";
import VectorSource from "ol/source/Vector";
import GeoTIFF from "ol/source/GeoTIFF";
import { Draw, Modify, Select, Translate } from "ol/interaction";
import Collection from "ol/Collection";
import Feature, { type FeatureLike } from "ol/Feature";
import Geometry from "ol/geom/Geometry";
import Point from "ol/geom/Point";
import MultiPoint from "ol/geom/MultiPoint";
import Polygon from "ol/geom/Polygon";
import MultiPolygon from "ol/geom/MultiPolygon";
import {
  pointerMove,
  platformModifierKeyOnly,
  shiftKeyOnly,
} from "ol/events/condition";
import { Circle, Fill, Stroke, Style, Text } from "ol/style";

import type { ImageMetadata, RadiometricParams } from "$lib/utils/types";
import type {
  AnnotateForm,
  AnnotateState,
  EquipmentData,
  ActivityData,
  AnnotateGeometry,
} from "$lib/states/annotate.svelte";

import frag from "$lib/shaders/slc_radiometric_correction_ol.frag.glsl?raw";

type ViewerMode = "draw" | "edit";

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

interface ViewerInteractions {
  hover: Select;
  select: Select;
  modify: Modify;
  translate: Translate;
  draw: Draw;
}

interface Options {
  image: ImageMetadata;
  radiometricParams: RadiometricParams | null;
  annotate: AnnotateState;
}

const MODE_INTERACTIONS = {
  edit: ["hover", "select", "modify", "translate"],
  draw: ["draw"],
} as const satisfies Record<ViewerMode, readonly (keyof ViewerInteractions)[]>;

export class ImageViewerState {
  #map: Map | null = null;
  #interactions!: ViewerInteractions;
  #sources: Record<AnnotateForm, VectorSource>;

  #selectedFeatures = $state<Feature[]>([]);

  constructor() {
    this.#sources = {
      equipment: new VectorSource(),
      activity: new VectorSource(),
    };
  }

  get selectedFeatures() {
    return this.#selectedFeatures;
  }

  attach(target: HTMLElement, options: Options) {
    if (this.#map) return;

    this.initMap(target, options);

    return () => {
      this.destroy();
    };
  }

  private destroy() {
    this.#map?.setTarget(undefined);
    this.#map?.getLayers().clear();
    this.#map?.dispose();
  }

  private initMap(target: HTMLElement, options: Options) {
    const rasterSource = new GeoTIFF({
      sources: [
        {
          url: "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/36/Q/WD/2020/7/S2A_36QWD_20200701_0_L2A/TCI.tif", //`http://localhost:8080/cog/${options.image.filename}.cog.tif`,
        },
      ],
    });
    const rasterStyle = options.radiometricParams
      ? ({
          fragmentShader: frag,
          uniforms: {
            u_noiseCoefs: options.radiometricParams.noise.poly.flat(),
            u_sigmaZeroCoefs: options.radiometricParams.sigma0.flat(),
          },
        } as RasterStyle)
      : undefined;

    const rasterLayer = new WebGLTileLayer({
      source: rasterSource,
      style: rasterStyle,
    });

    const equipmentLayer = new VectorLayer({
      source: this.#sources.equipment,
      style: (feature) => featureStyle(feature, equipmentColor, 0.7),
    });
    const activityLayer = new VectorLayer({
      source: this.#sources.activity,
      style: (feature) => {
        return featureStyle(feature, activityColor, 0.7, 0.0);
      },
    });

    this.#map = new Map({
      target: target,
      layers: [rasterLayer, equipmentLayer, activityLayer],
      view: rasterSource.getView(),
    });
    this.setupInteractions(options.annotate);
  }

  private setupInteractions(annotate: AnnotateState) {
    if (!this.#map) return;

    const modifiable = new Collection<Feature>();

    const hover = new Select({
      condition: pointerMove,
      hitTolerance: 5,
      filter: (feature) => !select.getFeatures().getArray().includes(feature),
      style: (feature) => featureStyle(feature, equipmentColor, 1.0, 0.0, 2),
    });

    const select: Select = new Select({
      addCondition: shiftKeyOnly,
      hitTolerance: 5,
      style: (feature) => {
        const features = select.getFeatures();
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

    const modify = new Modify({ features: modifiable });

    const translate = new Translate({
      condition: platformModifierKeyOnly,
      features: select.getFeatures(),
    });

    select.getFeatures().on("add", (e) => {
      const g = e.element.getGeometry();
      if (g instanceof Polygon || g instanceof MultiPolygon) {
        modifiable.push(e.element);
      }
      this.syncSelectedFeatures();
    });

    select.getFeatures().on("remove", (e) => {
      modifiable.remove(e.element);
      this.syncSelectedFeatures();
    });

    const draw = this.createDrawInteraction(annotate);

    this.#interactions = { hover, select, modify, translate, draw };

    Object.values(this.#interactions).forEach((i) =>
      this.#map!.addInteraction(i),
    );

    this.setMode(annotate.active ? "draw" : "edit");
  }

  private createDrawInteraction(annotate: AnnotateState) {
    const draw = new Draw({
      source: this.#sources[annotate.layer],
      type: annotate.geometry,
    });

    draw.on("drawend", (e) => {
      e.feature.setProperties({
        type: annotate.layer,
        label: annotate.label,
        data: structuredClone($state.snapshot(annotate.data)),
      });
    });
    return draw;
  }

  private setMode(mode: ViewerMode) {
    Object.values(this.#interactions).forEach((i) => i.setActive(false));

    for (const key of MODE_INTERACTIONS[mode]) {
      this.#interactions[key].setActive(true);
    }
  }

  private syncSelectedFeatures() {
    if (!this.#interactions.select) return;

    this.#selectedFeatures = [
      ...this.#interactions.select.getFeatures().getArray(),
    ];
  }

  updateDrawInteraction(annotate: AnnotateState) {
    if (!this.#map) return;

    if (this.#interactions.draw) {
      this.#map.removeInteraction(this.#interactions.draw);
    }

    const draw = this.createDrawInteraction(annotate);

    this.#interactions.draw = draw;
    this.#map.addInteraction(draw);

    this.setMode(annotate.active ? "draw" : "edit");
  }

  updateFeatureData(feature: Feature, data: EquipmentData | ActivityData) {
    const type = feature.get("type") as string | null;
    if (!type) return;

    const label =
      type === "equipment"
        ? `${data.id}\n${data.status}\n${data.confidence}`
        : "";

    feature.set("data", data);
    feature.set("label", label);
    feature.changed();

    this.syncSelectedFeatures();
  }

  deleteFeature(feature: Feature) {
    const type = feature.get("type");
    if (!type) return;

    const source = this.#sources[type];
    if (!source) return;

    const selected = this.#interactions.select.getFeatures();
    selected.remove(feature);
    this.syncSelectedFeatures();

    source.removeFeature(feature);
  }
}

const IMAGEVIEWER_KEY = Symbol("IMAGEVIEWER");

export function setImageViewerState() {
  const state = new ImageViewerState();
  return setContext(IMAGEVIEWER_KEY, state);
}

export function getImageViewerState() {
  const context =
    getContext<ReturnType<typeof setImageViewerState>>(IMAGEVIEWER_KEY);
  if (!context) {
    throw new Error("getAnnotateContext must be used within a provider");
  }
  return context;
}
