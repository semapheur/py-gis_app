import { getContext, setContext } from "svelte";
import { encode } from "@msgpack/msgpack";
import Map from "ol/Map";
import View from "ol/View";
import { transform, transformExtent } from "ol/proj";
import VectorLayer from "ol/layer/Vector";
import VectorSource from "ol/source/Vector";
import WebGLTileLayer from "ol/layer/WebGLTile";
import WebGLVectorLayer from "ol/layer/WebGLVector";
import GeoTIFF from "ol/source/GeoTIFF";
import { DragBox, Draw, Modify, Select, Translate } from "ol/interaction";
import Collection from "ol/Collection";
import Feature from "ol/Feature";
import {
  Geometry,
  SimpleGeometry,
  Point,
  LineString,
  Polygon,
  MultiPolygon,
} from "ol/geom";
import {
  containsCoordinate,
  createEmpty,
  extend,
  type Extent,
} from "ol/extent";
import { fromExtent } from "ol/geom/Polygon";
import {
  pointerMove,
  platformModifierKeyOnly,
  shiftKeyOnly,
  primaryAction,
  mouseOnly,
} from "ol/events/condition";
import { Style } from "ol/style";
import WKT from "ol/format/WKT";
import GeoJSON from "ol/format/GeoJSON";
import { type Coordinate, toStringHDMS } from "ol/coordinate";

import {
  type InteractionMode,
  type InteractionSet,
  type MeasurementType,
} from "$lib/contexts/ol_image_viewer/state.svelte";
import {
  styleText,
  styleMeasurement,
  styleAnnotationLabel,
  equipmentStyle,
  ghostStyle,
  defaultEnhancement,
  type Enhancement,
  formatArea,
  formatLength,
  styleSearchMarker,
} from "$lib/contexts/ol_image_viewer/styling";
import {
  //BandStretchManager,
  buildStyleExpression,
} from "$lib/contexts/ol_image_viewer/bandstretch_manager.svelte";
import { vertexStyle } from "$lib/utils/ol_styles";
import type { ImageInfo, RadiometricParams } from "$lib/utils/types";
import type {
  AnnotateForm,
  AnnotateState,
  AnnotationInfo,
  EquipmentData,
  ActivityData,
  AnnotationBaseInfo,
  ValidEquipmentData,
} from "$lib/contexts/annotate.svelte";
import { MGRS } from "$lib/utils/geo/mgrs";
import type { ImageId } from "$lib/utils/brand";
import { toLatLon, type CoordinateType } from "$lib/utils/geo/coord";

export type ContextMenuFeatureType = "equipment" | "measurement" | "ghost";

export interface ContextMenuFeature {
  type: ContextMenuFeatureType;
  features: Feature[];
  label: string;
}

export interface ContextMenuCoordinate {
  type: "coordinate";
  dms: string;
  mgrs: string;
  wkt: string;
}

export type ContextMenuItem = ContextMenuFeature | ContextMenuCoordinate;

interface ViewerInteractions {
  hover: Select;
  select: Select;
  modify: Modify;
  translate: Translate;
  draw: Draw | null;
  dragBox: DragBox | null;
}

interface Options {
  imageInfo: ImageInfo;
  radiometricParams: RadiometricParams | null;
  annotations?: AnnotationInfo[];
}

interface ZoomOptions {
  padding?: [number, number, number, number];
  maxZoom?: number;
  duration?: number;
  sourceProjection?: string;
}

export class ImageViewerController {
  #imageId: ImageId | null = null;
  #map: Map | null = null;
  #imageExtent: Extent | null = null;
  #maxZoomLevel: number = 0;
  //#bandStretch: BandStretchManager | null = null;
  #rasterLayer: WebGLTileLayer | null = null;
  #equipmentLayer: WebGLVectorLayer | null = null;
  #ghostLayer: WebGLVectorLayer | null = null;
  #activityLayer: VectorLayer | null = null;
  #labelLayers: Record<AnnotateForm | "ghost", VectorLayer | null>;
  #measurementLayer: VectorLayer | null = null;
  #interactions: Record<InteractionSet, ViewerInteractions | null>;
  #annotationSources: Record<AnnotateForm | "ghost", VectorSource>;
  #measurementSource = new VectorSource();
  #searchMarkerSource = new VectorSource();
  #searchMarkerLayer: VectorLayer | null = null;

  #equipmentFeatures = $state<Feature[]>([]);
  #selectedAnnotations = $state<Record<AnnotateForm, Feature[]>>({
    equipment: [],
    activity: [],
  });
  #hasSelectedAnnotations = $derived(
    this.#selectedAnnotations.activity.length +
      this.#selectedAnnotations.equipment.length >
      0,
  );
  enhancement = $state<Enhancement>({ ...defaultEnhancement });
  #contextMenu = $state<{
    x: number;
    y: number;
    items: ContextMenuItem[];
  } | null>(null);

  get projection() {
    return this.#map?.getView().getProjection() ?? null;
  }

  get selectedAnnotations() {
    return this.#selectedAnnotations;
  }

  get hasSelectedAnnotations(): boolean {
    return this.#hasSelectedAnnotations;
  }

  get equipmentFeatures() {
    return this.#equipmentFeatures;
  }

  get contextMenu() {
    return this.#contextMenu;
  }

  constructor() {
    this.#interactions = {
      annotation: null,
      ghost: null,
      measurement: null,
    };

    this.#labelLayers = {
      equipment: null,
      //activity: null,
      ghost: null,
    };

    this.#annotationSources = {
      equipment: new VectorSource(),
      ghost: new VectorSource(),
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

  #destroy() {
    if (this.#map === null) return;

    //this.#bandStretch?.stop();
    //this.#bandStretch = null;

    const interactions = this.#map.getInteractions().getArray();
    interactions.forEach((i) => {
      this.#map!.removeInteraction(i);
    });

    this.#annotationSources.equipment.clear();
    this.#annotationSources.activity.clear();
    this.#measurementSource.clear();
    this.#searchMarkerSource.clear();

    const layers = [
      this.#rasterLayer,
      this.#equipmentLayer,
      this.#ghostLayer,
      this.#activityLayer,
      this.#measurementLayer,
      this.#searchMarkerLayer,
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
    this.#ghostLayer = null;
    this.#activityLayer = null;
    this.#measurementLayer = null;
    this.#searchMarkerLayer = null;
    this.#equipmentFeatures = [];
    this.#selectedAnnotations = {
      equipment: [],
      activity: [],
    };
    this.#imageId = null;
    this.#imageExtent = null;
  }

  public attach(
    target: HTMLElement,
    options: Options,
    interactionSet: InteractionSet,
    interactionMode: InteractionMode,
  ) {
    if (this.#map) return;

    this.#setupMap(target, options, interactionSet, interactionMode);

    return () => {
      this.#destroy();
    };
  }

  async #setupMap(
    target: HTMLElement,
    options: Options,
    interactionSet: InteractionSet,
    interactionMode: InteractionMode,
  ) {
    if (!target) return;

    this.#imageId = options.imageInfo.id!;

    const url = `http://localhost:8080/cog/${options.imageInfo.filename}.cog.tif`;

    const rasterSource = new GeoTIFF({
      sources: [
        {
          url, //"https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/36/Q/WD/2020/7/S2A_36QWD_20200701_0_L2A/TCI.tif", //
        },
      ],
      normalize: false,
    });

    const viewOptions = await rasterSource.getView();

    if (!target || this.#map) return;

    const nativeResolutions = viewOptions.resolutions;
    if (!nativeResolutions) return;

    this.#imageExtent = viewOptions.extent ?? null;
    this.#maxZoomLevel = nativeResolutions.length - 1;

    const lastRes = nativeResolutions[nativeResolutions.length - 1];
    const extraLevels = 6;
    const extendedResolutions = [...nativeResolutions];

    for (let i = 1; i <= extraLevels; i++) {
      extendedResolutions.push(lastRes / Math.pow(2, i));
    }

    const rasterStyle = buildStyleExpression(options.imageInfo.band_statistics);

    this.#rasterLayer = new WebGLTileLayer({
      source: rasterSource,
      style: {
        variables: { ...defaultEnhancement },
        ...rasterStyle,
      },
    });
    this.#equipmentLayer = new WebGLVectorLayer({
      source: this.#annotationSources.equipment,
      style: equipmentStyle,
      variables: {
        hoverId: "",
      },
    });
    this.#ghostLayer = new WebGLVectorLayer({
      source: this.#annotationSources.ghost,
      style: ghostStyle,
      variables: {
        hoverId: "",
      },
    });

    this.#activityLayer = new VectorLayer({
      source: this.#annotationSources.activity,
      style: (feature) => styleAnnotation(feature, activityColor, 0.7, 0.0),
    });
    this.#labelLayers.equipment = new VectorLayer({
      source: this.#annotationSources.equipment,
      style: (feature) => styleAnnotationLabel(feature),
    });

    this.#labelLayers.ghost = new VectorLayer({
      source: this.#annotationSources.ghost,
      style: (feature) => styleAnnotationLabel(feature),
    });

    this.#measurementLayer = new VectorLayer({
      source: this.#measurementSource,
      style: (feature) => styleMeasurement(this.projection, feature, true),
    });

    this.#searchMarkerLayer = new VectorLayer({
      source: this.#searchMarkerSource,
      style: styleSearchMarker,
    });

    this.#map = new Map({
      target: target,
      controls: [],
      layers: [
        this.#rasterLayer,
        this.#equipmentLayer,
        this.#ghostLayer,
        this.#activityLayer,
        this.#measurementLayer,
        this.#searchMarkerLayer,
        ...Object.values(this.#labelLayers),
      ],
      view: new View({
        ...viewOptions,
        resolutions: extendedResolutions,
        constrainResolution: false,
      }),
    });

    //this.#bandStretch = new BandStretchManager(
    //  this.#rasterLayer,
    //  this.#map,
    //  url,
    //  {
    //    debounceMs: 400,
    //    lowPercentile: 2,
    //    highPercentile: 98,
    //    sampleSize: 256,
    //  },
    //);
    //this.#bandStretch.start();

    this.#setupAnnotationInteractions();
    this.#setupMeasurementInteractions();
    this.#setupGhostInteractions();

    this.updateInteraction(interactionSet, interactionMode);

    if (options.annotations?.length) {
      this.#loadAnnotations(options.annotations);
    }

    this.#setupContextMenu();
  }

  #setupAnnotationInteractions() {
    if (this.#map === null || this.#equipmentLayer === null) return;

    const handleFeatureEdit = async (features: Feature[]): Promise<void> => {
      const originalGeometries = features.map((feature) => ({
        feature,
        geometry: feature.getGeometry()?.clone(),
      }));

      try {
        await this.#persistFeatures(features, "edit");
      } catch (error) {
        originalGeometries.forEach(({ feature, geometry }) => {
          if (geometry) {
            feature.setGeometry(geometry);
          }
        });
        console.error("Failed to persist feature edits:", error);
      }
    };

    const handleHover = (features: Feature[]) => {
      const feature = features.length > 0 ? features[0] : null;
      const hoverId = feature ? feature.get("id") : "";

      this.#equipmentLayer?.updateStyleVariables({ hoverId });
    };

    const modifiable = new Collection<Feature>();

    const hover = new Select({
      condition: pointerMove,
      hitTolerance: 20,
      layers: [this.#equipmentLayer],
      filter: (feature) => !select.getFeatures().getArray().includes(feature),
      style: (feature) => styleAnnotationLabel(feature, true),
    });
    hover.on("select", (e) => {
      handleHover(e.selected);
    });

    const select: Select = new Select({
      addCondition: platformModifierKeyOnly,
      hitTolerance: 20,
      layers: [this.#equipmentLayer],
      style: (feature) => {
        const features = select.getFeatures();
        const index = features.getArray().indexOf(feature);
        const baseLabel = styleAnnotationLabel(feature, true);

        return index >= 0 && baseLabel
          ? [
              baseLabel,
              new Style({
                text: styleText(`${index + 1}`, "bold 10px sans-serif", 3, -15),
              }),
              vertexStyle,
            ]
          : baseLabel;
      },
    });

    select.getFeatures().on("add", (e) => {
      e.element.set("selected", 1);

      const g = e.element.getGeometry();
      if (g instanceof Polygon || g instanceof MultiPolygon) {
        modifiable.push(e.element);
      }

      this.#syncSelectedAnnotations();
    });
    select.getFeatures().on("remove", (e) => {
      e.element.set("selected", 0);
      modifiable.remove(e.element);
      this.#syncSelectedAnnotations();
    });

    const dragBox = new DragBox({
      condition: shiftKeyOnly,
    });

    dragBox.on("boxend", () => {
      const extent = dragBox.getGeometry().getExtent();

      [this.#annotationSources.equipment, this.#annotationSources.activity]
        .flatMap((source) => source.getFeaturesInExtent(extent))
        //.filter((f) => !select.getFeatures().getArray().includes(f));
        .forEach((f) => select.getFeatures().push(f));
    });

    dragBox.on("boxstart", () => {
      select.getFeatures().clear();
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

    this.#interactions.annotation = {
      hover,
      select,
      modify,
      translate,
      draw: null,
      dragBox,
    };
  }

  #setupMeasurementInteractions() {
    if (this.#map === null || this.#measurementLayer === null) return;

    const modifiable = new Collection<Feature>();

    const hover = new Select({
      condition: pointerMove,
      hitTolerance: 5,
      layers: [this.#measurementLayer],
      filter: (feature) => !select.getFeatures().getArray().includes(feature),
      style: (feature) =>
        styleMeasurement(this.projection, feature, true, true),
    });

    const select: Select = new Select({
      hitTolerance: 5,
      layers: [this.#measurementLayer],
      style: (feature) =>
        styleMeasurement(this.projection, feature, true, true, true),
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
      draw: null,
      dragBox: null,
    };
  }

  #setupGhostInteractions() {
    if (this.#map === null || this.#ghostLayer === null) return;

    const modifiable = new Collection<Feature>();

    const handleHover = (features: Feature[]) => {
      const feature = features.length > 0 ? features[0] : null;
      const hoverId = feature ? feature.get("id") : "";

      this.#ghostLayer?.updateStyleVariables({ hoverId });
    };

    const hover = new Select({
      condition: pointerMove,
      hitTolerance: 20,
      layers: [this.#ghostLayer],
      filter: (feature) => !select.getFeatures().getArray().includes(feature),
      style: (feature) => styleAnnotationLabel(feature, true),
    });
    hover.on("select", (e) => {
      handleHover(e.selected);
    });

    const select: Select = new Select({
      addCondition: shiftKeyOnly,
      hitTolerance: 20,
      layers: [this.#ghostLayer],
      style: (feature) => {
        const baseLabel = styleAnnotationLabel(feature, true);
        return [baseLabel, vertexStyle];
      },
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

    const dragBox = new DragBox({
      condition: shiftKeyOnly,
    });

    dragBox.on("boxend", () => {
      const extent = dragBox.getGeometry().getExtent();

      this.#annotationSources.ghost
        .getFeaturesInExtent(extent)
        .forEach((f) => select.getFeatures().push(f));
    });

    dragBox.on("boxstart", () => {
      select.getFeatures().clear();
    });

    const modify = new Modify({ features: modifiable });

    const translate = new Translate({
      condition: platformModifierKeyOnly,
      features: select.getFeatures(),
    });

    this.#interactions.ghost = {
      hover,
      select,
      modify,
      translate,
      draw: null,
      dragBox,
    };
  }

  #setupContextMenu() {
    if (this.#map === null) return;

    const getSelectedFeatures = (type: ContextMenuFeatureType): Feature[] => {
      switch (type) {
        case "equipment":
          return (
            this.#interactions.annotation?.select
              .getFeatures()
              .getArray()
              .filter((f) => f.get("type") === "equipment") ?? []
          );
        case "ghost":
          return (
            this.#interactions.ghost?.select.getFeatures().getArray() ?? []
          );
        case "measurement":
          return (
            this.#interactions.measurement?.select.getFeatures().getArray() ??
            []
          );
      }
    };

    const pluralLabel: Record<ContextMenuFeatureType, string> = {
      equipment: "equipment annotations",
      ghost: "ghosts",
      measurement: "measurements",
    };

    this.#map
      .getViewport()
      .addEventListener("contextmenu", (e: PointerEvent) => {
        e.preventDefault();

        const pixel = this.#map?.getEventPixel(e);
        if (!pixel) return;

        const layerChecks: Array<{
          layer: WebGLVectorLayer | VectorLayer | null;
          type: ContextMenuFeatureType;
          getLabel: (f: Feature) => string;
        }> = [
          {
            layer: this.#equipmentLayer,
            type: "equipment",
            getLabel: (f) => f.get("label"),
          },
          {
            layer: this.#ghostLayer,
            type: "ghost",
            getLabel: (f) => f.get("label"),
          },
          {
            layer: this.#measurementLayer,
            type: "measurement",
            getLabel: (f) => {
              const g = f.getGeometry();
              const projection = this.projection;
              if (!projection) return "";

              if (g instanceof Polygon)
                return `Area (${formatArea(g, projection)})`;
              if (g instanceof LineString)
                return `Length (${formatLength(g, projection)})`;
              return "";
            },
          },
        ];

        const items: ContextMenuItem[] = [];

        for (const { layer, type, getLabel } of layerChecks) {
          if (!layer) continue;
          const selected = getSelectedFeatures(type);
          let addedMultiForType = items.some(
            (i) => i.type == type && i.features.length > 1,
          );

          this.#map?.forEachFeatureAtPixel(
            pixel,
            (feature) => {
              const f = feature as Feature;
              if (selected.length > 1 && selected.includes(f)) {
                if (!addedMultiForType) {
                  items.push({
                    type,
                    features: selected,
                    label: `${selected.length} ${pluralLabel[type]}`,
                  });
                  addedMultiForType = true;
                }
                return;
              }
              items.push({
                type,
                features: [f],
                label: getLabel(f),
              });
            },
            { layerFilter: (l) => l === layer, hitTolerance: 10 },
          );
        }

        if (items.length === 0) {
          const coordinate = this.#map?.getCoordinateFromPixel(pixel);
          const projection = this.projection;
          if (!coordinate || !projection) {
            this.#contextMenu = null;
            return;
          }

          const lonlat = transform(coordinate, projection, "EPSG:4326");
          const [lon, lat] = lonlat;

          const point = new Point(lonlat);

          items.push({
            type: "coordinate",
            dms: toStringHDMS(lonlat),
            mgrs: MGRS.fromGeographic(lon, lat).toString(),
            wkt: new WKT().writeGeometry(point),
          });
        }

        this.#contextMenu = {
          x: e.clientX, //- rect.left,
          y: e.clientY, // - rect.top,
          items,
        };
      });

    this.#map.on("click", () => {
      this.#contextMenu = null;
    });
  }

  #createDrawAnnotationInteraction(annotateState: AnnotateState) {
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
          modifiedAtTimestamp: null,
        },
      });

      try {
        await this.#persistFeatures([e.feature], "draw");
        e.feature.set("label", annotateState.label);
      } catch (error) {
        source.removeFeature(e.feature);
        console.error("Failed to save annotation:", error);
      }
    });
    return draw;
  }

  #syncSelectedAnnotations() {
    if (!this.#interactions.annotation?.select) return;

    const selectedAnnotations: Record<AnnotateForm, Feature[]> = {
      equipment: [],
      activity: [],
    };

    for (const feature of this.#interactions.annotation.select
      .getFeatures()
      .getArray()) {
      const annotationType = feature.get("type") as AnnotateForm;

      if (!(annotationType in this.#selectedAnnotations)) continue;

      selectedAnnotations[annotationType].push(feature);
    }

    this.#selectedAnnotations = selectedAnnotations;
  }

  #loadAnnotations(records: AnnotationInfo[]) {
    if (this.#map === null || this.projection === null) return;

    const format = new GeoJSON({
      dataProjection: "EPSG:4326",
      featureProjection: this.projection,
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

  async #persistFeatures(features: Feature[], mode: "draw" | "edit") {
    const format = new WKT();
    const mapProjection = this.projection;

    const payload = features
      .map((feature) => {
        const geometry = feature.getGeometry();
        if (geometry === undefined) return null;

        const data = feature.get("data") as ValidEquipmentData;
        const metaData = feature.get("metaData");
        const geometry4326 = mapProjection
          ? geometry.clone().transform(mapProjection, "EPSG:4326")
          : geometry;

        return {
          type: feature.get("type"),
          data: {
            id: feature.get("id"),
            image: this.#imageId,
            geometry: format.writeGeometry(geometry4326),
            equipment: data.equipment.id,
            confidence: data.confidence.id,
            status: data.status.id,
            visibility: data.visibility.id,
            configuration: data.configuration.id,
            modification: data.modification?.map((m) => m.id) ?? [],
            camoflage: data.camoflage?.map((m) => m.id) ?? [],
            heading_deg: data.heading,
            speed_mps: data.speed,
            createdByUserId: metaData.createdByUserId,
            modifiedByUserId: mode === "edit" ? "" : metaData.modifiedByUserId,
            createdAtTimestamp: metaData.createdAtTimestamp,
            modifiedAtTimestamp:
              mode === "edit" ? Date.now() : metaData.modifiedAtTimestamp,
          },
        };
      })
      .filter(Boolean);

    if (!payload.length) return;

    const response = await fetch("/api/update-annotations", {
      method: "POST",
      headers: { "Content-Type": "application/msgpack" },
      body: encode(payload),
    });

    if (!response.ok) {
      throw new Error(`Failed to persist features: ${response.statusText}`);
    }
  }

  public updateInteraction(set: InteractionSet, mode: InteractionMode) {
    if (this.#map === null || this.#interactions === null) return;

    for (const key of Object.keys(this.#interactions) as InteractionSet[]) {
      if (key === set) continue;
      const other = this.#interactions[key];
      if (!other) continue;
      Object.values(other).forEach((i) => {
        if (i) this.#map?.removeInteraction(i);
      });
    }

    const interactions = this.#interactions[set];
    if (!interactions) return;

    const { draw, ...editInteractions } = interactions;

    if (mode === "draw") {
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

  public updateDrawAnnotationInteraction(
    annotateState: AnnotateState,
    isActive: boolean,
  ) {
    if (this.#map === null || this.#interactions.annotation === null) return;

    if (this.#interactions.annotation.draw) {
      this.#map.removeInteraction(this.#interactions.annotation.draw);
    }

    const draw = this.#createDrawAnnotationInteraction(annotateState);

    this.#interactions.annotation.draw = draw;
    this.#map.addInteraction(draw);
    draw.setActive(isActive);
  }

  public updateDrawMeasurementInteraction(
    type: MeasurementType,
    isActive: boolean,
  ) {
    if (
      this.#map === null ||
      this.projection === null ||
      this.#interactions.measurement === null
    )
      return;

    if (this.#interactions.measurement.draw) {
      this.#map.removeInteraction(this.#interactions.measurement.draw);
    }

    const drawType = type === "length" ? "LineString" : "Polygon";
    const draw = new Draw({
      source: this.#measurementSource,
      type: drawType,
      condition: (e) => primaryAction(e) && mouseOnly(e),
      style: (feature) => styleMeasurement(this.projection!, feature, true),
    });

    this.#interactions.measurement.draw = draw;
    this.#map.addInteraction(draw);
    draw.setActive(isActive);
  }

  public removeMeasurements(features: Feature[]) {
    this.#measurementSource.removeFeatures(features);
  }

  public clearMeasurements() {
    this.#measurementSource.clear();
  }

  public addGhosts(records: AnnotationBaseInfo[]) {
    if (this.#map === null || this.projection === null) return;

    this.clearGhosts();

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
    this.#annotationSources.ghost.addFeatures(features);
  }

  public async acceptGhosts(features: Feature[]) {
    for (const feature of features) {
      feature.setProperties({
        id: crypto.randomUUID(),
        metaData: {
          createdByUserId: "",
          modifiedByUserId: null,
          createdAtTimestamp: Date.now(),
          modifiedAtTimestamp: null,
        },
      });
    }

    this.#annotationSources.ghost.removeFeatures(features);
    this.#annotationSources.equipment.addFeatures(features);
    await this.#persistFeatures(features, "draw");
  }

  public removeGhosts(features: Feature[]) {
    this.#annotationSources.ghost.removeFeatures(features);
  }

  public clearGhosts() {
    this.#annotationSources.ghost.clear();
  }

  public applyEnhancement() {
    if (this.#rasterLayer === null) return;

    this.#rasterLayer.updateStyleVariables({
      brightness: this.enhancement.brightness,
      contrast: this.enhancement.contrast,
      exposure: this.enhancement.exposure,
      saturation: this.enhancement.saturation,
      gamma: this.enhancement.gamma,
    });
  }

  public resetEnhancement() {
    if (this.#rasterLayer === null) return;

    this.enhancement = { ...defaultEnhancement };
  }

  public updateFeatureData(
    feature: Feature,
    data: EquipmentData | ActivityData,
  ) {
    const type = feature.get("type") as string | null;
    if (!type) return;

    const label =
      type === "equipment"
        ? `${data.equipment?.label}\n${data.confidence.label}`
        : "";

    feature.setProperties({
      data,
      label,
    });
    feature.changed();

    this.#syncSelectedAnnotations();
    this.#persistFeatures([feature], "edit");
  }

  public async convertPointFeaturesToPolygons(
    features: Feature[],
    sizeMeters: number = 3,
  ) {
    const mapProjection = this.projection;
    if (!mapProjection) return;

    const pointFeatures = features.filter(
      (f) => f.getGeometry() instanceof Point,
    );

    if (!pointFeatures.length) return;

    const conversions = pointFeatures.map((feature) => {
      const point = feature.getGeometry() as Point;
      const coords = point.getCoordinates();

      const [mx, my] = transform(coords, mapProjection, "EPSG:3857");
      const half = sizeMeters / 2;
      const squareCoordsMeters = [
        [
          [mx - half, my - half],
          [mx + half, my - half],
          [mx + half, my + half],
          [mx - half, my + half],
          [mx - half, my - half],
        ],
      ];

      const squareCoords = [
        squareCoordsMeters[0].map((c) =>
          transform(c, "EPSG:3857", mapProjection),
        ),
      ];
      const polygon = new Polygon(squareCoords);

      const metaData = $state.snapshot(feature.get("metaData"));
      const oldMetaData = structuredClone(metaData);
      const modifiedAtTimestamp = Date.now();

      return {
        feature,
        point,
        polygon,
        oldMetaData,
        modifiedAtTimestamp,
      };
    });

    for (const { feature, polygon, modifiedAtTimestamp } of conversions) {
      feature.setGeometry(polygon);
      const metaData = feature.get("metaData");
      metaData.modifiedByUserId = "";
      metaData.modifiedAtTimestamp = modifiedAtTimestamp;
      feature.setProperties({ metaData });
      feature.changed();
    }
    this.#syncSelectedAnnotations();

    const format = new WKT();
    const payload = conversions.map(
      ({ feature, polygon, modifiedAtTimestamp }) => ({
        id: feature.get("id"),
        geometry: format.writeGeometry(polygon),
        modifiedByUserId: "",
        modifiedAtTimestamp: modifiedAtTimestamp,
      }),
    );

    try {
      const response = await fetch("/api/convert-annotation", {
        method: "POST",
        headers: { "Content-Type": "application/msgpack" },
        body: encode({ conversions: payload }),
      });

      if (!response.ok) {
        throw new Error(`Failed to persist features: ${response.statusText}`);
      }
    } catch (error) {
      for (const { feature, point, oldMetaData } of conversions) {
        feature.setGeometry(point);
        feature.setProperties(oldMetaData);
        feature.changed();
      }
      this.#syncSelectedAnnotations();
      console.error("Failed to convert features to polygons:", error);
    }
  }

  public removeAnnotations(features: Feature[]) {
    if (this.#interactions.annotation === null) return;

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

    this.#syncSelectedAnnotations();

    if (Object.keys(payload).length === 0) return;

    fetch("/api/delete-annotations", {
      method: "POST",
      headers: { "Content-Type": "application/msgpack" },
      body: encode(payload),
    });
  }

  public selectAllAnnotations(annotationType: AnnotateForm) {
    if (this.#interactions.annotation === null) return;

    const select = this.#interactions.annotation.select;
    const source = this.#annotationSources[annotationType];

    select.getFeatures().clear();
    source.getFeatures().forEach((f) => select.getFeatures().push(f));
  }

  public getViewExtentWkt(): string | null {
    if (this.#map === null) return null;

    const view = this.#map.getView();
    const extent = view.calculateExtent(this.#map.getSize());
    const extent4326 = transformExtent(
      extent,
      view.getProjection(),
      "EPSG:4326",
    );
    const polygon = fromExtent(extent4326);

    return new WKT().writeGeometry(polygon);
  }

  public zoomToGeometry(geometry: SimpleGeometry, options: ZoomOptions = {}) {
    if (this.#map === null || this.projection === null) return;

    const target =
      options.sourceProjection && options.sourceProjection !== this.projection
        ? geometry.clone().transform(options.sourceProjection, this.projection)
        : geometry;

    this.#map.getView().fit(target, {
      padding: options.padding ?? [50, 50, 50, 50],
      maxZoom: options.maxZoom,
      duration: options.duration ?? 100,
    });
  }

  public zoomToFeatures(features: Feature[], options: ZoomOptions = {}) {
    if (!features.length) return;

    const geometries = features
      .map((f) => f.getGeometry())
      .filter((g): g is Geometry => g !== undefined);

    if (!geometries.length) return;

    const extent = geometries.reduce(
      (acc, g) => extend(acc, g.getExtent()),
      createEmpty(),
    );

    this.zoomToGeometry(fromExtent(extent), options);
  }

  public goToCoordinate(coordinate: Coordinate): boolean {
    if (this.#map === null || this.projection === null) return false;

    const mapCoordinate = transform(coordinate, "EPSG:4326", this.projection);

    if (
      this.#imageExtent &&
      !containsCoordinate(this.#imageExtent, mapCoordinate)
    ) {
      return false;
    }

    this.#searchMarkerSource.clear();
    const feature = new Feature({ geometry: new Point(mapCoordinate) });
    feature.set("label", toStringHDMS(coordinate));
    this.#searchMarkerSource.addFeature(feature);

    this.#map.getView().animate({
      center: mapCoordinate,
      zoom: this.#maxZoomLevel,
      duration: 300,
    });

    return true;
  }

  public clearSearchMarker() {
    this.#searchMarkerSource.clear();
  }

  public closeContextMenu() {
    this.#contextMenu = null;
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
