import { getContext, setContext } from "svelte";
import Map from "ol/Map";
import WebGLTileLayer, { type Style as RasterStyle } from "ol/layer/WebGLTile";
import VectorLayer from "ol/layer/Vector";
import VectorSource from "ol/source/Vector";
import GeoTIFF from "ol/source/GeoTIFF";
import { Draw, Modify, Select, Translate } from "ol/interaction";
import Collection from "ol/Collection";
import Feature from "ol/Feature";
import { Point, LineString, Polygon, MultiPolygon } from "ol/geom";
import {
  pointerMove,
  platformModifierKeyOnly,
  shiftKeyOnly,
} from "ol/events/condition";
import { Style } from "ol/style";
import WKT from "ol/format/WKT";
import GeoJSON from "ol/format/GeoJSON";

import {
  ImageViewerState,
  type InteractionMode,
  type InteractionSet,
  type MeasurementType,
} from "$lib/contexts/image_viewer/state.svelte";
import {
  styleAnnotation,
  styleAnnotationText,
  styleMeasurement,
  vertexStyle,
  equipmentColor,
} from "$lib/contexts/image_viewer/styling";
import type { ImageInfo, RadiometricParams } from "$lib/utils/types";
import type {
  AnnotateForm,
  AnnotateState,
  AnnotationInfo,
  EquipmentData,
  ActivityData,
} from "$lib/contexts/annotate.svelte";

import frag from "$lib/shaders/slc_radiometric_correction_ol.frag.glsl?raw";

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
  annotations?: AnnotationInfo[];
}

const MODE_INTERACTIONS = {
  edit: ["hover", "select", "modify", "translate"],
  draw: ["draw"],
} as const satisfies Record<
  InteractionMode,
  readonly (keyof ViewerInteractions)[]
>;

export class ImageViewerController {
  #image: string | null = null;
  #map: Map | null = null;
  #rasterLayer: WebGLTileLayer | null = null;
  #equipmentLayer: VectorLayer | null = null;
  #activityLayer: VectorLayer | null = null;
  #measurementLayer: VectorLayer | null = null;
  #interactions: Record<InteractionSet, ViewerInteractions | null>;
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

  public attach(target: HTMLElement, ctx: ImageViewerState, options: Options) {
    if (this.#map) return;

    this.setupMap(target, options);

    $effect(() => {
      this.applyInteractionMode(ctx.activeSet, ctx.activeMode);
    });

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

    this.setupAnnotationInteractions();
    this.setupMeasurementInteractions();
    this.setInteractionMode("annotation", "edit");

    if (options.annotations?.length) {
      this.loadAnnotations(options.annotations);
    }
  }

  private setupAnnotationInteractions() {
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

    //Object.values(this.#interactions.annotation).forEach((i) =>
    //  this.#map!.addInteraction(i),
    //);
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

    //Object.values(this.#interactions.measurement).forEach((i) =>
    //  this.#map!.addInteraction(i),
    //);
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

  private applyInteractionMode(set: InteractionSet, mode: InteractionMode) {
    if (!this.#map || !this.#interactions) return;

    const interactions = this.#interactions[set];
    const otherSet = set === "annotation" ? "measurement" : "annotation";
    const otherInteractions = this.#interactions[otherSet];

    if (otherInteractions) {
      Object.values(otherInteractions).forEach((i) => {
        if (i) this.#map?.removeInteraction(i);
      });
    }

    if (!interactions) return;

    const { draw, ...editInteractions } = interactions;

    if (mode == "draw") {
      Object.values(editInteractions).forEach((i) => {
        if (i) this.#map?.removeInteraction(i);
      });
      if (draw) this.#map.addInteraction(draw);
    } else {
      if (draw) this.#map.removeInteraction(draw);
      Object.values(editInteractions).forEach((i) => {
        if (i) this.#map?.addInteraction(i);
      });
    }
  }

  private setInteractionMode(layer: InteractionSet, mode: InteractionMode) {
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

  public startDrawInteraction(layer: InteractionSet) {
    this.setInteractionMode(layer, "draw");
  }

  public stopDrawInteraction(layer: InteractionSet) {
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
        metaData: record.metaData,
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

    feature.setProperties({
      data,
      label,
    });
    feature.changed();

    this.syncSelectedFeatures();
    this.persistFeatures([feature], "edit");
  }

  public async convertPointFeatureToPolygon(
    feature: Feature,
    sizeMeters: number = 3,
  ) {
    const point = feature.getGeometry();

    if (!point || !(point instanceof Point)) {
      throw new Error("Feature must have a Point geometry");
    }

    const [x, y] = point.getCoordinates();
    const half = sizeMeters / 2;
    const squareCoords = [
      [
        [x - half, y - half],
        [x + half, y - half],
        [x + half, y + half],
        [x - half, y + half],
        [x - half, y - half], // close the ring
      ],
    ];
    const polygon = new Polygon(squareCoords);

    feature.setGeometry(polygon);
    const metaData = feature.get("metaData");
    const oldMetaData = structuredClone(metaData);
    metaData.modifiedByUserId = "";
    metaData.modifiedAtTimestamp = Date.now();
    feature.setProperties({
      metaData,
    });
    feature.changed();

    this.syncSelectedFeatures();

    const format = new WKT();
    const payload = {
      id: feature.get("id"),
      geometry: format.writeGeometry(polygon),
      modifiedByUserId: metaData.modifiedByUserId,
      modifiedAtTimestamp: metaData.modifiedAtTimestamp,
    };

    try {
      const response = await fetch("/api/convert-annotation", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`Failed to persist features: ${response.statusText}`);
      }
    } catch (error) {
      feature.setGeometry(point);
      feature.setProperties(oldMetaData);
      feature.changed();
      this.syncSelectedFeatures();
      throw error;
    }
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

const VIEWER_CONTROLLER_KEY = Symbol("VIEWER_CONTROLLER");

export function setImageViewerController() {
  const state = new ImageViewerController();
  return setContext(VIEWER_CONTROLLER_KEY, state);
}

export function getImageViewerController() {
  const context = getContext<ReturnType<typeof setImageViewerController>>(
    VIEWER_CONTROLLER_KEY,
  );
  if (!context) {
    throw new Error("getImageViewerController must be used within a provider");
  }
  return context;
}
