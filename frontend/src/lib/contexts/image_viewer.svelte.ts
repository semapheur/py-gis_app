import { getContext, setContext } from "svelte";
import Map from "ol/Map";
import WebGLTileLayer, { type Style as RasterStyle } from "ol/layer/WebGLTile";
import VectorLayer from "ol/layer/Vector";
import VectorSource from "ol/source/Vector";
import GeoTIFF from "ol/source/GeoTIFF";
import { Draw, Modify, Select, Translate } from "ol/interaction";
import Collection from "ol/Collection";
import Feature, { type FeatureLike } from "ol/Feature";
import { Projection } from "ol/proj";
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
import { Circle, Fill, Stroke, Style, Text, RegularShape } from "ol/style";
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

type InteractionMode = "draw" | "edit";
type InteractionLayer = "annotation" | "measurement";

export const measureOptions = ["Area", "Length"] as const;
export type MeasurementType = Lowercase<(typeof measureOptions)[number]>;

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
  draw?: Draw;
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

const measurementStyle = new Style({
  fill: new Fill({
    color: "rgba(255, 255, 255, 0.2)",
  }),
  stroke: new Stroke({
    color: "rgba(0, 0, 0, 0.5)",
    lineDash: [10, 10],
    width: 2,
  }),
  image: new Circle({
    radius: 5,
    stroke: new Stroke({
      color: "rgba(0, 0, 0, 0.7)",
    }),
    fill: new Fill({
      color: "rgba(255, 255, 255, 0.2)",
    }),
  }),
});

const measurementLabelStyle = new Style({
  text: new Text({
    fill: new Fill({
      color: "rgba(255, 255, 255, 1)",
    }),
    backgroundFill: new Fill({
      color: "rgba(0, 0, 0, 0.7)",
    }),
    padding: [3, 3, 3, 3],
    textBaseline: "bottom",
    offsetY: -15,
  }),
  image: new RegularShape({
    radius: 8,
    points: 3,
    angle: Math.PI,
    displacement: [0, 10],
    fill: new Fill({
      color: "rgba(0, 0, 0, 0.7)",
    }),
  }),
});

const measurementSegmentStyle = new Style({
  text: new Text({
    fill: new Fill({
      color: "rgba(255, 255, 255, 1)",
    }),
    backgroundFill: new Fill({
      color: "rgba(0, 0, 0, 0.4)",
    }),
    padding: [2, 2, 2, 2],
    textBaseline: "bottom",
    offsetY: -12,
  }),
  image: new RegularShape({
    radius: 6,
    points: 3,
    angle: Math.PI,
    displacement: [0, 8],
    fill: new Fill({
      color: "rgba(0, 0, 0, 0.4)",
    }),
  }),
});

function formatLength(line: LineString, projection: Projection): string {
  const length = getLength(line, { projection });

  const output =
    length > 1000
      ? `${(length / 1000).toFixed(2)} km`
      : `${length.toFixed(2)} m`;

  return output;
}

function formatArea(polygon: Polygon, projection: Projection): string {
  const area = getArea(polygon, { projection });

  const output =
    area > 10000
      ? `${(area / 1000000).toFixed(2)} km²`
      : `${area.toFixed(2)} m²`;

  return output;
}

function styleAnnotationText(
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

function styleAnnotation(
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
      text: label ? styleAnnotationText(label, textColor, 1.0, 25) : undefined,
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
      text: label ? styleAnnotationText(label, textColor, 1.0, 10) : undefined,
    });
  }

  return null;
}

function styleMeasurement(
  projection: Projection,
  feature: FeatureLike,
  segments: boolean,
) {
  const styles = [measurementStyle];
  const geometry = feature.getGeometry();
  if (!geometry) return styles;

  const type = geometry.getType();

  let point: Point | undefined;
  let label: string | undefined;
  let line: LineString | undefined;

  if (type === "Polygon") {
    const polygon = geometry as Polygon;
    point = polygon.getInteriorPoint();
    label = formatArea(polygon, projection);
    line = new LineString(polygon.getCoordinates()[0]);
  } else if (type === "LineString") {
    const lineString = geometry as LineString;
    point = new Point(lineString.getLastCoordinate());
    label = formatLength(lineString, projection);
    line = lineString;
  }

  if (segments && line) {
    line.forEachSegment((a, b) => {
      const segment = new LineString([a, b]);
      const segmentLabel = formatLength(segment, projection);
      const segmentPoint = new Point(segment.getCoordinateAt(0.5));

      const segmentStyle = measurementSegmentStyle.clone();
      segmentStyle.setGeometry(segmentPoint);
      segmentStyle.getText()?.setText(segmentLabel);
      styles.push(segmentStyle);
    });
  }

  if (label && point) {
    const labelStyle = measurementLabelStyle.clone();
    labelStyle.setGeometry(point);
    labelStyle.getText().setText(label);
    styles.push(labelStyle);
  }

  return styles;
}

const vertexStyle = new Style({
  image: new Circle({
    radius: 3,
    fill: new Fill({ color: "#fff" }),
    stroke: new Stroke({ color: "#000", width: 1 }),
  }),
  geometry: (feature: FeatureLike) => {
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
} as const satisfies Record<
  InteractionMode,
  readonly (keyof ViewerInteractions)[]
>;

export class ImageViewerState {
  #image: string | null = null;
  #map: Map | null = null;
  #rasterLayer: WebGLTileLayer | null = null;
  #equipmentLayer: VectorLayer | null = null;
  #activityLayer: VectorLayer | null = null;
  #measurementLayer: VectorLayer | null = null;
  #interactions: Record<InteractionLayer, ViewerInteractions | null>;
  #annotationSources: Record<AnnotateForm, VectorSource>;
  #measurementSource = new VectorSource();

  #equipmentFeatures = $state<Feature[]>([]);
  #selectedFeatures = $state<Feature[]>([]);

  constructor() {
    this.#interactions = {
      annotation: null,
      measurement: null,
    };

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
    if (!this.#map) return;

    const interactions = this.#map.getInteractions().getArray();
    interactions.forEach((i) => {
      this.#map!.removeInteraction(i);
    });

    this.#annotationSources.equipment.clear();
    this.#annotationSources.activity.clear();
    this.#measurementSource.clear();

    const layers = [
      this.#rasterLayer,
      this.#equipmentLayer,
      this.#activityLayer,
      this.#measurementLayer,
    ];

    layers.forEach((layer) => {
      if (layer) {
        layer.setSource(null);
        layer.dispose();
      }
    });

    this.#map.getLayers().clear();
    this.#map.setTarget(undefined);
    this.#map.dispose();

    this.#map = null;
    this.#rasterLayer = null;
    this.#equipmentLayer = null;
    this.#activityLayer = null;
    this.#measurementLayer = null;
    this.#equipmentFeatures = [];
    this.#selectedFeatures = [];
    this.#image = null;
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
    this.#equipmentLayer = new VectorLayer({
      source: this.#annotationSources.equipment,
      style: (feature) => styleAnnotation(feature, equipmentColor, 0.7),
    });
    this.#activityLayer = new VectorLayer({
      source: this.#annotationSources.activity,
      style: (feature) => styleAnnotation(feature, activityColor, 0.7, 0.0),
    });
    this.#measurementLayer = new VectorLayer({
      source: this.#measurementSource,
      style: (feature) => styleMeasurement(this.projection, feature, true),
    });

    this.#map = new Map({
      target: target,
      layers: [
        this.#rasterLayer,
        this.#equipmentLayer,
        this.#activityLayer,
        this.#measurementLayer,
      ],
      view: rasterSource.getView(),
    });

    this.setupAnnotationInteractions(options.annotateState);
    this.setupMeasurementInteractions();
    this.setInteractionMode("annotation", "edit");

    if (options.annotations?.length) {
      this.loadAnnotations(options.annotations);
    }
  }

  private setupAnnotationInteractions(annotateState: AnnotateState) {
    if (!this.#map || !this.#activityLayer || !this.#equipmentLayer) return;

    const handleFeatureEdit = async (features: Feature[]): Promise<void> => {
      const originalGeometries = features.map((feature) => ({
        feature,
        geometry: feature.getGeometry()?.clone(),
      }));

      try {
        await this.persistFeatures(features, "edit");
      } catch (error) {
        originalGeometries.forEach(({ feature, geometry }) => {
          if (geometry) {
            feature.setGeometry(geometry);
          }
        });
        console.error("Failed to persist feature edits:", error);
      }
    };

    const modifiable = new Collection<Feature>();

    const hover = new Select({
      condition: pointerMove,
      hitTolerance: 5,
      layers: [this.#activityLayer, this.#equipmentLayer],
      filter: (feature) => !select.getFeatures().getArray().includes(feature),
      style: (feature) => styleAnnotation(feature, equipmentColor, 1.0, 0.0, 2),
    });

    const select: Select = new Select({
      addCondition: shiftKeyOnly,
      hitTolerance: 5,
      layers: [this.#activityLayer, this.#equipmentLayer],
      style: (feature) => {
        const features = select.getFeatures();
        const index = features.getArray().indexOf(feature);
        const base = styleAnnotation(feature, equipmentColor, 1.0, 0.2, 2);

        return index >= 0 && base
          ? [
              base,
              new Style({
                text: styleAnnotationText(`${index + 1}`, textColor, 1.0, -15),
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
      handleFeatureEdit(e.features.getArray());
    });

    const translate = new Translate({
      condition: platformModifierKeyOnly,
      features: select.getFeatures(),
    });
    translate.on("translateend", (e) => {
      handleFeatureEdit(e.features.getArray());
    });

    //const draw = this.createDrawAnnotationInteraction(annotateState);

    this.#interactions.annotation = {
      hover,
      select,
      modify,
      translate,
    };

    Object.values(this.#interactions.annotation).forEach((i) =>
      this.#map!.addInteraction(i),
    );
  }

  private setupMeasurementInteractions() {
    if (!this.#map || !this.#measurementLayer) return;

    const modifiable = new Collection<Feature>();

    const hover = new Select({
      condition: pointerMove,
      hitTolerance: 5,
      layers: [this.#measurementLayer],
      filter: (feature) => !select.getFeatures().getArray().includes(feature),
    });

    const select: Select = new Select({
      hitTolerance: 5,
      layers: [this.#measurementLayer],
      style: (feature) => styleMeasurement(this.projection, feature, true),
    });

    select.getFeatures().on("add", (e) => {
      const g = e.element.getGeometry();
      if (g instanceof LineString || g instanceof Polygon) {
        modifiable.push(e.element);
      }
    });
    select.getFeatures().on("remove", (e) => {
      modifiable.remove(e.element);
    });

    const modify = new Modify({
      features: modifiable,
      style: (feature) => styleMeasurement(this.projection, feature, true),
    });

    const translate = new Translate({
      condition: platformModifierKeyOnly,
      features: select.getFeatures(),
    });

    this.#interactions.measurement = {
      hover,
      select,
      modify,
      translate,
    };

    Object.values(this.#interactions.measurement).forEach((i) =>
      this.#map!.addInteraction(i),
    );
  }

  private createDrawAnnotationInteraction(annotateState: AnnotateState) {
    const draw = new Draw({
      source: this.#annotationSources[annotateState.layer],
      type: annotateState.geometry,
    });

    draw.on("drawend", async (e) => {
      const source = this.#annotationSources[annotateState.layer];

      e.feature.setProperties({
        id: crypto.randomUUID(),
        type: annotateState.layer,
        label: "Saving...",
        data: $state.snapshot(annotateState.data),
        metaData: {
          createdByUserId: "",
          modifiedByUserId: null,
          createdAtTimestamp: Date.now(),
          modifiedAtTimestmap: null,
        },
      });

      try {
        await this.persistFeatures([e.feature], "draw");
        e.feature.set("label", annotateState.label);
      } catch (error) {
        source.removeFeature(e.feature);
        console.error("Failed to save annotation:", error);
      }
    });
    return draw;
  }

  public updateDrawAnnotationInteraction(
    annotateState: AnnotateState,
    isActive: boolean,
  ) {
    if (!this.#map || !this.#interactions.annotation) return;

    if (this.#interactions.annotation.draw) {
      this.#map.removeInteraction(this.#interactions.annotation.draw);
    }

    const draw = this.createDrawAnnotationInteraction(annotateState);

    this.#interactions.annotation.draw = draw;
    this.#map.addInteraction(draw);
    draw.setActive(isActive);
  }

  public updateDrawMeasurementInteraction(
    type: MeasurementType,
    isActive: boolean,
  ) {
    if (!this.#map || !this.projection || !this.#interactions.measurement)
      return;

    if (this.#interactions.measurement.draw) {
      this.#map.removeInteraction(this.#interactions.measurement.draw);
    }

    const drawType = type === "length" ? "LineString" : "Polygon";
    const draw = new Draw({
      source: this.#measurementSource,
      type: drawType,
      style: (feature) => styleMeasurement(this.projection!, feature, true),
    });

    this.#interactions.measurement.draw = draw;
    this.#map.addInteraction(draw);
    draw.setActive(isActive);
  }

  public clearMeasurements() {
    this.#measurementSource.clear();
  }

  private setInteractionMode(layer: InteractionLayer, mode: InteractionMode) {
    if (!this.#interactions.annotation || !this.#interactions.measurement)
      return;

    Object.values(this.#interactions.annotation).forEach((i) =>
      i.setActive(false),
    );

    Object.values(this.#interactions.measurement).forEach((i) =>
      i.setActive(false),
    );

    for (const key of MODE_INTERACTIONS[mode]) {
      this.#interactions[layer][key]?.setActive(true);
    }
  }

  public startDrawInteraction(layer: InteractionLayer) {
    this.setInteractionMode(layer, "draw");
  }

  public stopDrawInteraction(layer: InteractionLayer) {
    this.setInteractionMode(layer, "edit");
  }

  private syncSelectedFeatures() {
    if (!this.#interactions.annotation?.select) return;

    this.#selectedFeatures = [
      ...this.#interactions.annotation.select.getFeatures().getArray(),
    ];
  }

  private loadAnnotations(records: AnnotationInfo[]) {
    if (!this.#map || !this.projection) return;

    const format = new GeoJSON({
      featureProjection: this.projection,
      dataProjection: this.projection,
    });

    const features: Feature[] = [];
    for (const record of records) {
      const geometry = format.readGeometry(record.geometry);
      const feature = new Feature({ geometry });

      feature.setProperties({
        id: record.id,
        type: "equipment",
        label: record.label,
        data: record.data,
      });
      features.push(feature);
    }
    this.#annotationSources.equipment.addFeatures(features);
  }

  private async persistFeatures(features: Feature[], mode: "draw" | "edit") {
    const format = new WKT();

    const payload = features
      .map((feature) => {
        const geometry = feature.getGeometry();
        if (geometry === undefined) return null;

        const data = feature.get("data");
        const metaData = feature.get("metaData");

        return {
          type: feature.get("type"),
          data: {
            id: feature.get("id"),
            image: this.#image,
            equipment: data.equipment.id,
            confidence: data.confidence.id,
            status: data.status.id,
            geometry: format.writeGeometry(geometry),
            createdByUserId: metaData.createdByUserId,
            modifiedByUserId: mode === "edit" ? "" : metaData.modifiedByUserId,
            createdAtTimestamp: metaData.createdAtTimestamp,
            modifiedAtTimestamp:
              mode === "edit" ? Date.now() : metaData.modifiedByUserId,
          },
        };
      })
      .filter(Boolean);

    if (!payload.length) return;

    const response = await fetch("/api/update-annotations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`Failed to persist features: ${response.statusText}`);
    }
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
    if (!this.#interactions.annotation) return;

    const selected = this.#interactions.annotation.select.getFeatures();
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
