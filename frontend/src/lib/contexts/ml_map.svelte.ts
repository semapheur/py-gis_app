import { getContext, setContext } from "svelte";
import * as maplibre from "maplibre-gl";
import { bboxToWkt, type BBox } from "$lib/utils/geo/bbox";
import { type ImagePreviewInfo } from "$lib/utils/types";
import {
  buildMapLibreStyle,
  type MapConfig,
  type LayerInfo,
} from "$lib/utils/map/layers";

type Coordinates = [
  [number, number],
  [number, number],
  [number, number],
  [number, number],
];

interface PolygonLink {
  geometry: GeoJSON.Polygon;
  label: string;
  href: string;
}

interface PolygonStyle {
  lineColor?: string;
  lineWidth?: number;
  lineDasharray?: number[];
  fillColor?: string;
  fillOpacity?: number;
}

interface PointStyle {
  radius?: number;
  color?: string;
  strokeColor?: string;
  strokeWidth?: number;
}

export class MapLibreState {
  #map: maplibre.Map | null = $state(null);
  #layers: LayerInfo[] = $state([]);
  #initialExtent: BBox | null = null;
  #isLoaded: boolean = false;
  #resizeObserver: ResizeObserver | null = null;

  constructor(initialBbox?: BBox | null) {
    this.#initialExtent = initialBbox ?? null;
  }

  destroy() {
    this.#resizeObserver?.disconnect();
    this.#map?.remove();
  }

  public get layers() {
    return this.#layers;
  }

  private async initMap(target: HTMLElement) {
    const response = await fetch("map_config.json");
    const mapConfig = (await response.json()) as MapConfig;
    const { sources, layers } = buildMapLibreStyle(mapConfig.layers);

    this.#layers = mapConfig.layers.map((layer, i: number) => ({
      id: layer.id,
      label: layer.label,
      visible: i === 0,
    }));

    const map = new maplibre.Map({
      container: target,
      style: {
        version: 8,
        sources,
        layers,
      },
    });

    map.addControl(new maplibre.NavigationControl(), "top-right");

    map.on("load", () => {
      this.#isLoaded = true;
      this.applyInitialExtent();
    });

    this.#map = map;

    const resizeObserver = new ResizeObserver(() => {
      if (map) map.resize();
    });
    resizeObserver.observe(target);
    this.#resizeObserver = resizeObserver;
  }

  private applyInitialExtent() {
    if (!this.#map || !this.#initialExtent) return;

    const bbox = this.#initialExtent;
    this.#map.fitBounds(bbox, { animate: false });
  }

  private upsertImageSource(
    id: string,
    url: string,
    coordinates: Coordinates,
    beforeId?: string,
  ) {
    if (!this.#map) return;

    const src = this.#map.getSource(id) as maplibre.ImageSource | undefined;

    if (src) {
      src.updateImage({ url, coordinates });
      return;
    }

    this.#map.addSource(id, { type: "image", url, coordinates });
    this.#map.addLayer({ id, type: "raster", source: id }, beforeId);
  }

  private upsertSource(
    sourceId: string,
    data: GeoJSON.FeatureCollection | GeoJSON.Feature,
  ): boolean {
    if (!this.#map) return false;

    const src = this.#map.getSource(sourceId) as
      | maplibre.GeoJSONSource
      | undefined;

    if (src) {
      src.setData(data);
      return false;
    }

    this.#map.addSource(sourceId, { type: "geojson", data });
    return true;
  }

  private setPolygons(
    sourceId: string,
    polygons: GeoJSON.Polygon[],
    style: PolygonStyle = {},
    beforeId?: string,
  ) {
    if (!this.#map) return;

    const {
      lineColor = "#007aff",
      lineWidth = 2,
      lineDasharray,
      fillColor,
      fillOpacity = 0.1,
    } = style;

    const data: GeoJSON.FeatureCollection = {
      type: "FeatureCollection",
      features: polygons.map((polygon) => ({
        type: "Feature",
        geometry: polygon,
        properties: {},
      })),
    };

    const isNew = this.upsertSource(sourceId, data);
    if (!isNew) return;

    const lineLayer: maplibre.LayerSpecification = {
      id: `${sourceId}-line`,
      type: "line",
      source: sourceId,
      paint: {
        "line-color": lineColor,
        "line-width": lineWidth,
        ...(lineDasharray && { "line-dasharray": lineDasharray }),
      },
    };

    this.#map.addLayer(lineLayer, beforeId);
    if (fillColor) {
      this.#map.addLayer(
        {
          id: `${sourceId}-fill`,
          type: "fill",
          source: sourceId,
          paint: {
            "fill-color": fillColor,
            "fill-opacity": fillOpacity,
          },
        },
        beforeId,
      );
    }
  }

  private setPoints(
    sourceId: string,
    points: GeoJSON.Point[],
    style: PointStyle = {},
  ) {
    if (!this.#map) return;

    const {
      radius = 6,
      color = "#ff3b30",
      strokeColor = "#ffffff",
      strokeWidth = 2,
    } = style;

    const data: GeoJSON.FeatureCollection = {
      type: "FeatureCollection",
      features: points.map((point) => ({
        type: "Feature",
        geometry: point,
        properties: {},
      })),
    };

    const isNew = this.upsertSource(sourceId, data);
    if (!isNew) return;

    this.#map.addLayer({
      id: sourceId,
      type: "circle",
      source: sourceId,
      paint: {
        "circle-radius": radius,
        "circle-color": color,
        "circle-stroke-color": strokeColor,
        "circle-stroke-width": strokeWidth,
      },
    });
  }

  private decimalsForZoom(zoom: number): number {
    if (zoom >= 15) return 6;
    if (zoom >= 12) return 5;
    if (zoom >= 9) return 4;
    if (zoom >= 6) return 3;
    return 2;
  }

  private getBounds(coords: GeoJSON.Position[]): maplibre.LngLatBoundsLike {
    const lats = coords.map((c) => c[1]);
    const lons = coords.map((c) => c[0]);
    return [
      [Math.min(...lons), Math.min(...lats)],
      [Math.max(...lons), Math.max(...lats)],
    ];
  }

  private reorderPolygon(coords: GeoJSON.Position[]): Coordinates | null {
    if (!this.#map) return null;
    // Maplibre order: top-left, top-right, bottom-right, bottom left

    if (coords.length === 5) coords = coords.slice(0, 4);

    // project into screen space
    const points = coords.map(([lon, lat]) => {
      const p = this.#map.project([lon, lat]);
      return { lon, lat, x: p.x, y: p.y, angle: 0 };
    });

    // centroid in screen space
    const cx = points.reduce((s, p) => s + p.x, 0) / points.length;
    const cy = points.reduce((s, p) => s + p.y, 0) / points.length;

    // sort counterclockwise around centroid in screen space
    points.forEach((p) => {
      p.angle = Math.atan2(p.y - cy, p.x - cx);
    });
    points.sort((a, b) => a.angle - b.angle);

    let topLeftIndex = 0;
    let bestScore = Infinity;

    points.forEach((p, i) => {
      const score = p.y * 1e5 + p.x;
      if (score < bestScore) {
        bestScore = score;
        topLeftIndex = i;
      }
    });

    const ordered = [
      points[topLeftIndex],
      points[(topLeftIndex + 1) % 4],
      points[(topLeftIndex + 2) % 4],
      points[(topLeftIndex + 3) % 4],
    ];

    return ordered.map((p) => [p.lon, p.lat]) as Coordinates;
  }

  public attach(element: HTMLElement) {
    this.initMap(element);

    return () => {
      this.destroy();
    };
  }

  public setInitialExtent(bbox: BBox | null) {
    this.#initialExtent = bbox;

    if (this.#map && this.#map.loaded() && bbox) {
      this.applyInitialExtent();
    }
  }

  public fitToPolygon(
    coords: GeoJSON.Position[],
    options?: maplibre.FitBoundsOptions,
  ) {
    if (!this.#map) return;

    const bounds = this.getBounds(coords);
    this.#map.fitBounds(bounds, { padding: 40, ...options });
  }

  public setImagePreview(preview: ImagePreviewInfo) {
    if (!this.#map) return;

    if (!this.#isLoaded) {
      this.#map.once("load", () => this.setImagePreview(preview));
      return;
    }

    const coords = preview.polygon.coordinates[0];
    const ordered = this.reorderPolygon(coords);
    if (!ordered) return;

    const url = `/thumbnails/${preview.filename}.png`;

    this.upsertImageSource("image-preview", url, ordered, "search-extent-line");
    const style = {};
    this.setPolygons(
      "footprint",
      [preview.polygon],
      style,
      "search-extent-line",
    );

    this.fitToPolygon(coords, {
      bearing: preview.azimuth_angle,
      pitch: preview.look_angle,
      animate: true,
      duration: 500,
    });
  }

  public getCurrentBbox(): BBox | null {
    if (!this.#map) return null;

    const bounds = this.#map.getBounds();

    const bbox: BBox = [
      bounds.getWest(),
      bounds.getSouth(),
      bounds.getEast(),
      bounds.getNorth(),
    ];

    return bbox;
  }

  public getCurrentExtentWkt(): string | null {
    if (!this.#map) return null;

    const bbox = this.getCurrentBbox();
    if (!bbox) return null;

    const zoom = this.#map.getZoom();

    return bboxToWkt(bbox, this.decimalsForZoom(zoom));
  }

  public zoomToPoint(
    sourceId: string,
    point: GeoJSON.Point,
    options?: Partial<maplibre.FlyToOptions>,
  ) {
    if (!this.#map) return;

    const style = {};

    this.setPoints(sourceId, [point]);

    this.#map.flyTo({
      center: point.coordinates,
      zoom: 14,
      speed: 4.0,
      curve: 1.0,
      essential: true,
      ...options,
    });
  }

  public zoomToPolygon(
    sourceId: string,
    polygon: GeoJSON.Polygon,
    options?: Partial<maplibre.FlyToOptions>,
  ) {
    if (!this.#map) return;

    if (!this.#isLoaded) {
      this.#map.once("load", () =>
        this.zoomToPolygon(sourceId, polygon, options),
      );
      return;
    }

    const style = {};

    this.setPolygons(sourceId, [polygon]);
    const coords = polygon.coordinates[0];
    this.fitToPolygon(coords, options);
  }

  public setPolygonLinks(features: PolygonLink[]) {
    if (!this.#map) return;

    if (!this.#isLoaded) {
      this.#map.once("load", () => this.setPolygonLinks(features));
      return;
    }

    const sourceId = "polygon-links";
    const fillLayerId = `${sourceId}-fill`;
    const lineLayerId = `${sourceId}-line`;
    const labelLayerId = `${sourceId}-label`;

    const geojson: GeoJSON.FeatureCollection = {
      type: "FeatureCollection",
      features: features.map((f) => ({
        type: "Feature",
        geometry: f.geometry,
        properties: {
          label: f.label,
          href: f.href,
        },
      })),
    };

    const existingSource = this.#map.getSource(sourceId) as
      | maplibre.GeoJSONSource
      | undefined;

    if (existingSource) {
      existingSource.setData(geojson);
      return;
    }

    this.#map.addSource(sourceId, {
      type: "geojson",
      data: geojson,
    });

    this.#map.addLayer({
      id: fillLayerId,
      type: "fill",
      source: sourceId,
      paint: {
        "fill-color": "#007aff",
        "fill-opacity": 0.25,
      },
    });

    this.#map.addLayer({
      id: lineLayerId,
      type: "line",
      source: sourceId,
      paint: {
        "line-color": "#007aff",
        "line-width": 2,
      },
    });

    this.#map.addLayer({
      id: labelLayerId,
      type: "symbol",
      source: sourceId,
      layout: {
        "text-field": ["get", "label"],
        "text-size": 14,
        "text-anchor": "center",
      },
      paint: {
        "text-color": "#111",
        "text-halo-color": "#ffffff",
        "text-halo-width": 2,
      },
    });

    this.#map.on("click", fillLayerId, (e) => {
      const feature = e.features?.[0];
      const link = feature?.properties?.href;

      if (link) {
        window.location.href = link;
      }
    });

    // Pointer cursor
    this.#map.on("mouseenter", fillLayerId, () => {
      this.#map!.getCanvas().style.cursor = "pointer";
    });

    this.#map.on("mouseleave", fillLayerId, () => {
      this.#map!.getCanvas().style.cursor = "";
    });
  }

  public selectLayer(id: string) {
    if (!this.#map) return;

    for (const layer of this.#layers) {
      layer.visible = layer.id === id;

      this.#map.setLayoutProperty(
        layer.id,
        "visibility",
        layer.visible ? "visible" : "none",
      );
    }
  }

  public onMoveEnd(callback: (bbox: string) => void): () => void {
    if (!this.#map) return () => {};

    const handler = () => {
      const bbox = this.getCurrentBbox();
      if (!bbox) return;

      callback(bbox.join(","));
    };

    this.#map.on("moveend", handler);
    return () => this.#map?.off("moveend", handler);
  }
}

const MAPLIBRE_KEY = Symbol("MAPLIBRE");

export function setMapLibreState(initialBbox?: BBox | null) {
  const state = new MapLibreState(initialBbox);
  return setContext(MAPLIBRE_KEY, state);
}

export function getMapLibreState() {
  const context = getContext<ReturnType<typeof setMapLibreState>>(MAPLIBRE_KEY);
  if (!context) {
    throw new Error("getMapLibreState must be used within a provider");
  }
  return context;
}
