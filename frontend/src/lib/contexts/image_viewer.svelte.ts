import { getContext, setContext } from "svelte";
import Map from "ol/Map";
import WebGLTileLayer, { type Style as RasterStyle } from "ol/layer/WebGLTile";
import VectorLayer from "ol/layer/Vector";
import VectorSource from "ol/source/Vector";
import GeoTIFF from "ol/source/GeoTIFF";
import { Draw, Modify, Select, Translate } from "ol/interaction";
import Collection from "ol/Collection";
import Feature, { type FeatureLike } from "ol/Feature";
import Overlay from "ol/Overlay";
import {
  Geometry,
  Point,
  LineString,
  Polygon,
  MultiPoint,
  MultiPolygon,
} from "ol/geom";
import { getArea, getLength } from "ol/sphere";
import {
  pointerMove,
  platformModifierKeyOnly,
  shiftKeyOnly,
} from "ol/events/condition";
import { Circle, Fill, Stroke, Style, Text } from "ol/style";
import WKT from "ol/format/WKT";
import GeoJSON from "ol/format/GeoJSON";

import type { ImageInfo, RadiometricParams } from "$lib/utils/types";
import type {
  AnnotateForm,
  AnnotateState,
  AnnotationInfo,
  EquipmentData,
  ActivityData,
} from "$lib/contexts/annotate.svelte";

import frag from "$lib/shaders/slc_radiometric_correction_ol.frag.glsl?raw";
import { unByKey } from "ol/Observable";

type ViewerMode = "draw" | "edit";
type MeasurementType = "length" | "area";

export interface Enhancement {
  brightness: number;
  contrast: number;
  exposure: number;
  saturation: number;
  gamma: number;
}

interface ViewerInteractions {
  hover: Select;
  select: Select;
  modify: Modify;
  translate: Translate;
  draw: Draw;
  measureDraw?: Draw;
}

interface Options {
  imageInfo: Partial<ImageInfo>;
  radiometricParams: RadiometricParams | null;
  annotateState: AnnotateState;
  annotations?: AnnotationInfo[];
}

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

const MODE_INTERACTIONS = {
  edit: ["hover", "select", "modify", "translate"],
  draw: ["draw"],
} as const satisfies Record<ViewerMode, readonly (keyof ViewerInteractions)[]>;

export class ImageViewerState {
  #image: string | null = null;
  #map: Map | null = null;
  #rasterLayer: WebGLTileLayer | null = null;
  #interactions!: ViewerInteractions;
  #annotationSources: Record<AnnotateForm, VectorSource>;
  #measurementSource = new VectorSource();
  #measurementOverlay: Overlay | null = null;
  #measurementListener: ReturnType<typeof on> | null = null;

  #equipmentFeatures = $state<Feature[]>([]);
  #selectedFeatures = $state<Feature[]>([]);

  constructor() {
    this.#annotationSources = {
      equipment: new VectorSource(),
      activity: new VectorSource(),
    };

    this.#annotationSources.equipment.on("addfeature", () => {
      this.#equipmentFeatures = this.#annotationSources.equipment
        .getFeatures()
        .slice();
    });

    this.#annotationSources.equipment.on("removefeature", () => {
      this.#equipmentFeatures = this.#annotationSources.equipment
        .getFeatures()
        .slice();
    });

    if (typeof document !== "undefined") {
      const overlayElement = document.createElement("div");
      overlayElement.className = "measurement-tooltip";
      overlayElement.style.cssText = `
            position: absolute;
            background: rgba(0, 0, 0, 0.7);
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            pointer-events: none;
            white-space: nowrap;
          `;

      this.#measurementOverlay = new Overlay({
        element: overlayElement,
        offset: [0, -15],
        positioning: "bottom-center",
      });
    }
  }

  get projection() {
    return this.#map?.getView().getProjection() ?? null;
  }

  get selectedFeatures() {
    return this.#selectedFeatures;
  }

  get equipmentFeatures() {
    return this.#equipmentFeatures;
  }

  private destroy() {
    this.#map?.setTarget(undefined);
    this.#map?.getLayers().clear();
    this.#map?.dispose();
  }

  public attach(target: HTMLElement, options: Options) {
    if (this.#map) return;

    this.setupMap(target, options);

    return () => {
      this.destroy();
    };
  }

  private setupMap(target: HTMLElement, options: Options) {
    this.#image = options.imageInfo.id!;

    const rasterSource = new GeoTIFF({
      sources: [
        {
          url: "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/36/Q/WD/2020/7/S2A_36QWD_20200701_0_L2A/TCI.tif", //`http://localhost:8080/cog/${options.imageInfo.filename}.cog.tif`,
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

    this.#rasterLayer = new WebGLTileLayer({
      source: rasterSource,
    });

    const equipmentLayer = new VectorLayer({
      source: this.#annotationSources.equipment,
      style: (feature) => featureStyle(feature, equipmentColor, 0.7),
    });
    const activityLayer = new VectorLayer({
      source: this.#annotationSources.activity,
      style: (feature) => {
        return featureStyle(feature, activityColor, 0.7, 0.0);
      },
    });

    const measurementLayer = new VectorLayer({
      source: this.#measurementSource,
      style: new Style({
        stroke: new Stroke({
          color: "rgba(255, 0, 0, 0.8)",
          width: 2,
          lineDash: [10, 10],
        }),
        fill: new Fill({
          color: "rgba(255, 0, 0, 0.1)",
        }),
        image: new Circle({
          radius: 5,
          fill: new Fill({
            color: "rgba(255, 0, 0, 0.8)",
          }),
        }),
      }),
    });

    this.#map = new Map({
      target: target,
      layers: [
        this.#rasterLayer,
        equipmentLayer,
        activityLayer,
        measurementLayer,
      ],
      view: rasterSource.getView(),
    });

    if (this.#measurementOverlay) {
      this.#map.addOverlay(this.#measurementOverlay);
    }

    this.setupInteractions(options.annotateState);

    if (options.annotations?.length) {
      this.loadAnnotations(options.annotations);
    }
  }

  private setupInteractions(annotateState: AnnotateState) {
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

    const modify = new Modify({ features: modifiable });
    modify.on("modifyend", (e) => {
      this.persistFeatures(e.features.getArray(), "edit");
    });

    const translate = new Translate({
      condition: platformModifierKeyOnly,
      features: select.getFeatures(),
    });
    translate.on("translateend", (e) => {
      this.persistFeatures(e.features.getArray(), "edit");
    });

    const draw = this.createDrawInteraction(annotateState);

    this.#interactions = { hover, select, modify, translate, draw };

    Object.values(this.#interactions).forEach((i) =>
      this.#map!.addInteraction(i),
    );

    this.setMode(annotateState.active ? "draw" : "edit");
  }

  private createDrawInteraction(annotateState: AnnotateState) {
    const draw = new Draw({
      source: this.#annotationSources[annotateState.layer],
      type: annotateState.geometry,
    });

    draw.on("drawend", (e) => {
      e.feature.setProperties({
        id: crypto.randomUUID(),
        type: annotateState.layer,
        label: annotateState.label,
        data: {
          ...$state.snapshot(annotateState.data),
          createdByUserId: "",
          modifiedByUserId: null,
          createdAtTimestamp: Date.now(),
          modifiedAtTimestmap: null,
        },
      });

      this.persistFeatures([e.feature], "draw");
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

  private loadAnnotations(records: AnnotationInfo[]) {
    if (!this.#map || !this.projection) return;

    const format = new GeoJSON({
      featureProjection: this.projection,
      dataProjection: this.projection,
    });

    for (const record of records) {
      const geometry = format.readGeometry(record.geometry);
      const feature = new Feature({ geometry });

      feature.setProperties({
        id: record.id,
        type: "equipment",
        label: record.label,
        data: record.data,
      });

      this.#annotationSources.equipment.addFeature(feature);
    }
  }

  private persistFeatures(features: Feature[], mode: "draw" | "edit") {
    const format = new WKT();

    const payload = features
      .map((feature) => {
        const geometry = feature.getGeometry();
        if (geometry === undefined) return null;

        const data = feature.get("data");

        return {
          type: feature.get("type"),
          data: {
            id: feature.get("id"),
            image: this.#image,
            equipment: data.equipment.id,
            confidence: data.confidence.id,
            status: data.status.id,
            geometry: format.writeGeometry(geometry),
            createdByUserId: data.createdByUserId,
            modifiedByUserId: mode === "edit" ? "" : data.modifiedByUserId,
            createdAtTimestamp: data.createdAtTimestamp,
            modifiedAtTimestamp:
              mode === "edit" ? Date.now() : data.modifiedByUserId,
          },
        };
      })
      .filter(Boolean);

    if (!payload.length) return;

    fetch("/api/update-annotations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  }

  public updateEnhancement(enhancement: Enhancement) {
    if (!this.#rasterLayer) return;

    this.#rasterLayer.setStyle({
      color: ["array", ["band", 1], ["band", 2], ["band", 3], 1],
      brightness: enhancement.brightness,
      contrast: enhancement.contrast,
      exposure: enhancement.exposure,
      saturation: enhancement.saturation,
      gamma: enhancement.gamma,
    });
  }

  public updateDrawInteraction(annotateState: AnnotateState) {
    if (!this.#map) return;

    if (this.#interactions.draw) {
      this.#map.removeInteraction(this.#interactions.draw);
    }

    const draw = this.createDrawInteraction(annotateState);

    this.#interactions.draw = draw;
    this.#map.addInteraction(draw);

    this.setMode(annotateState.active ? "draw" : "edit");
  }

  public updateFeatureData(
    feature: Feature,
    data: EquipmentData | ActivityData,
  ) {
    const type = feature.get("type") as string | null;
    if (!type) return;

    const label =
      type === "equipment"
        ? `${data.equipment?.label}\n${data.confidence.label}\n${data.status.label}`
        : "";

    feature.set("data", data);
    feature.set("label", label);
    feature.changed();

    this.syncSelectedFeatures();
    this.persistFeatures([feature], "edit");
  }

  public removeFeatures(features: Feature[]) {
    const selected = this.#interactions.select.getFeatures();
    const payload: Record<string, string[]> = {};

    for (const feature of features) {
      const annotationType = feature.get("type") as AnnotateForm | null;
      if (!annotationType) continue;

      const source = this.#annotationSources[annotationType];
      if (!source) continue;

      selected.remove(feature);
      source.removeFeature(feature);

      const geometryType = feature.getGeometry()?.getType();
      if (!geometryType) continue;

      const id = feature.get("id");

      const key = `${annotationType}_${geometryType.toLowerCase()}`;
      (payload[key] ??= []).push(id);
    }

    this.syncSelectedFeatures();

    if (Object.keys(payload).length === 0) return;

    fetch("/api/delete-annotations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  }

  private formatLength(line: LineString): string {
    const length = getLength(line, {
      projection: this.projection || undefined,
    });

    const output =
      length > 1000
        ? `${(length / 1000).toFixed(2)} km`
        : `${length.toFixed(2)} m`;

    return output;
  }

  private formatArea(polygon: Polygon): string {
    const area = getArea(polygon, { projection: this.projection || undefined });

    const output =
      area > 10000
        ? `${(area / 1000000).toFixed(2)} km²`
        : `${area.toFixed(2)} m²`;

    return output;
  }

  public startMeasurement(type: MeasurementType) {
    if (!this.#map) return;

    this.#measurementSource.clear();

    if (this.#interactions.measureDraw) {
      this.#map.removeInteraction(this.#interactions.measureDraw);
    }

    this.setMode("edit");
    Object.values(this.#interactions).forEach((i) => i.setActive(false));

    const drawType = type === "length" ? "LineString" : "Polygon";
    const measureDraw = new Draw({
      source: this.#measurementSource,
      type: drawType,
      style: new Style({
        stroke: new Stroke({
          color: "rgba(255, 0, 0, 0.8)",
          width: 2,
          lineDash: [10, 10],
        }),
        fill: new Fill({
          color: "rgba(255, 0, 0, 0.1)",
        }),
        image: new Circle({
          radius: 5,
          fill: new Fill({
            color: "rgba(255, 0, 0, 0.8)",
          }),
        }),
      }),
    });

    let sketch: Feature | null = null;
    const tooltipElement = this.#measurementOverlay?.getElement();

    measureDraw.on("drawstart", (e) => {
      sketch = e.feature;

      this.#measurementListener = sketch.getGeometry()!.on("change", (e) => {
        const geom = e.target;
        let tooltipText = "";

        if (geom instanceof Polygon) {
          tooltipText = this.formatArea(geom);
          this.#measurementOverlay?.setPosition(
            geom.getInteriorPoint().getCoordinates(),
          );
        } else if (geom instanceof LineString) {
          tooltipText = this.formatLength(geom);
          this.#measurementOverlay?.setPosition(geom.getLastCoordinate());
        }

        if (tooltipElement) {
          tooltipElement.innerHTML = tooltipText;
        }
      });
    });

    measureDraw.on("drawend", (e) => {
      if (tooltipElement) {
        tooltipElement.className = "measurement-tooltip measurement-static";
      }

      if (this.#measurementListener) {
        unByKey(this.#measurementListener);
      }

      sketch = null;

      const feature = e.feature;
      const geom = feature.getGeometry();
      let tooltipText = "";
      let position: number[] = [];

      if (geom instanceof Polygon) {
        tooltipText = this.formatArea(geom);
        position = geom.getInteriorPoint().getCoordinates();
      } else if (geom instanceof LineString) {
        tooltipText = this.formatLength(geom);
        position = geom.getLastCoordinate();
      }

      feature.set("measurement", tooltipText);
    });

    this.#interactions.measureDraw = measureDraw;
    this.#map.addInteraction(measureDraw);
  }

  public stopMeasurement() {
    if (!this.#map) return;

    if (this.#interactions.measureDraw) {
      this.#map.removeInteraction(this.#interactions.measureDraw);
      delete this.#interactions.measureDraw;
    }

    if (this.#measurementListener) {
      unByKey(this.#measurementListener);
      this.#measurementListener = null;
    }

    if (this.#measurementOverlay) {
      this.#measurementOverlay.setPosition(undefined);
    }

    this.setMode("edit");
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
    throw new Error("getImageViewerState must be used within a provider");
  }
  return context;
}
