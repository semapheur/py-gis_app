import { getContext, setContext } from "svelte";
import * as maplibre from "maplibre-gl";
import { bboxToWkt, type BBox } from "$lib/utils/geo/bbox";
import { type ImagePreviewInfo } from "$lib/utils/types";

type Coordinates = [
  [number, number],
  [number, number],
  [number, number],
  [number, number],
];

export class MapLibreState {
  #map: maplibre.Map | null = null;
  #resizeObserver: ResizeObserver | null = null;
  #initialExtent: GeoJSON.Polygon | null = null;

  destroy() {
    this.#resizeObserver?.disconnect();
    this.#map?.remove();
  }

  private initMap(target: HTMLElement) {
    const map = new maplibre.Map({
      container: target,
      style: {
        version: 8,
        sources: {
          osm: {
            type: "raster",
            tiles: ["https://a.tile.openstreetmap.org/{z}/{x}/{y}.png"],
            tileSize: 256,
            attribution: "&copy; OpenStreetMap Contributors",
            maxzoom: 19,
          },
        },
        layers: [
          {
            id: "osm",
            type: "raster",
            source: "osm", // This must match the source key above
          },
        ],
      },
    });

    map.addControl(new maplibre.NavigationControl(), "top-right");

    map.on("load", () => {
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

    const coords = this.#initialExtent.coordinates[0];
    this.fitToPolygon(coords, { animate: false });
  }

  private upsertImageSource(id: string, url: string, coordinates: Coordinates) {
    if (!this.#map) return;

    const src = this.#map.getSource(id) as maplibre.ImageSource | undefined;

    if (src) {
      src.updateImage({ url, coordinates });
    } else {
      this.#map.addSource(id, { type: "image", url, coordinates });
      this.#map.addLayer({ id, type: "raster", source: id });
    }
  }

  private upsertFootprint(coords: GeoJSON.Position[]) {
    if (!this.#map) return;

    const src = this.#map.getSource("footprint") as
      | maplibre.GeoJSONSource
      | undefined;

    const data = {
      type: "Polygon",
      coordinates: [coords],
    };

    if (src) {
      src.setData(data);
    } else {
      this.#map.addSource("footprint", { type: "geojson", data });
      this.#map.addLayer({
        id: "footprint",
        type: "line",
        source: "footprint",
        paint: {
          "line-color": "#f4320b",
          "line-width": 3,
        },
      });
    }
  }

  private upsertZoomPoint(lat: number, lon: number) {
    if (!this.#map) return;

    const data: GeoJSON.Feature<GeoJSON.Point> = {
      type: "Feature",
      geometry: {
        type: "Point",
        coordinates: [lon, lat],
      },
      properties: {},
    };

    const src = this.#map.getSource("zoom-point") as
      | maplibre.GeoJSONSource
      | undefined;

    if (src) {
      src.setData(data);
    } else {
      this.#map.addSource("zoom-point", {
        type: "geojson",
        data,
      });

      this.#map.addLayer({
        id: "zoom-point",
        type: "circle",
        source: "zoom-point",
        paint: {
          "circle-radius": 6,
          "circle-color": "#ff3b30",
          "circle-stroke-color": "#ffffff",
          "circle-stroke-width": 2,
        },
      });
    }
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
    const lngs = coords.map((c) => c[0]);
    return [
      [Math.min(...lngs), Math.min(...lats)],
      [Math.max(...lngs), Math.max(...lats)],
    ];
  }

  private reorderFootprint(coords: GeoJSON.Position[]): Coordinates {
    if (!this.#map) return;
    // Maplibre order: top-left, top-right, bottom-right, bottom left

    if (coords.length === 5) coords = coords.slice(0, 4);

    // project into screen space
    const points = coords.map(([lng, lat]) => {
      const p = this.#map.project([lng, lat]);
      return { lng, lat, x: p.x, y: p.y, angle: 0 };
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

    return ordered.map((p) => [p.lng, p.lat]) as Coordinates;
  }

  public attach(element: HTMLElement) {
    this.initMap(element);

    return () => {
      this.destroy();
    };
  }

  public setInitialExtent(extent: GeoJSON.Polygon | null) {
    this.#initialExtent = extent;

    if (this.#map && this.#map.loaded() && extent) {
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
    const ordered = this.reorderFootprint(preview.coordinates);
    const url = `/thumbnails/${preview.filename}.png`;

    this.upsertImageSource("image-preview", url, ordered);
    this.upsertFootprint(preview.coordinates);

    this.fitToPolygon(preview.coordinates, {
      bearing: preview.azimuth_angle,
      pitch: preview.look_angle,
      animate: true,
      duration: 500,
    });
  }

  public getCurrentExtentWkt(): string {
    if (!this.#map) return;

    const bounds = this.#map.getBounds();
    const zoom = this.#map.getZoom();

    const bbox: BBox = [
      bounds.getWest(),
      bounds.getSouth(),
      bounds.getEast(),
      bounds.getNorth(),
    ];

    return bboxToWkt(bbox, this.decimalsForZoom(zoom));
  }

  public zoomToLatLon(
    lat: number,
    lon: number,
    options?: Partial<maplibre.FlyToOptions>,
  ) {
    if (!this.#map) return;

    this.upsertZoomPoint(lat, lon);

    this.#map.flyTo({
      center: [lon, lat],
      zoom: 14,
      speed: 4.0,
      curve: 1.0,
      essential: true,
      ...options,
    });
  }
}

const MAPLIBRE_KEY = Symbol("MAPLIBRE");

export function setMapLibreState() {
  const state = new MapLibreState();
  return setContext(MAPLIBRE_KEY, state);
}

export function getMapLibreState() {
  const context = getContext<ReturnType<typeof setMapLibreState>>(MAPLIBRE_KEY);
  if (!context) {
    throw new Error("getMapLibreState must be used within a provider");
  }
  return context;
}
