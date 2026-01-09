<script lang="ts">
  import * as maplibre from "maplibre-gl";
  import "maplibre-gl/dist/maplibre-gl.css";
  import { type ImagePreviewInfo } from "$lib/utils/types";
  import { bboxToWkt, type BBox } from "$lib/utils/geo/geometry";

  type Coordinates = [
    [number, number],
    [number, number],
    [number, number],
    [number, number],
  ];

  interface Props {
    extent?: GeoJSON.Polygon | null;
    imagePreview?: ImagePreviewInfo | null;
    showSearchButton?: boolean;
    onSearchExtent?: (polygonWkt: string) => void;
  }

  let {
    extent = null,
    imagePreview = null,
    showSearchButton = false,
    onSearchExtent,
  }: Props = $props();

  let mapLoaded = $state<boolean>(false);

  let map: maplibre.Map;
  let resizeObserver: ResizeObserver;

  function decimalsForZoom(zoom: number): number {
    if (zoom >= 15) return 6;
    if (zoom >= 12) return 5;
    if (zoom >= 9) return 4;
    if (zoom >= 6) return 3;
    return 2;
  }

  function reorderFootprint(
    coords: GeoJSON.Position[],
    map: maplibre.Map,
  ): Coordinates {
    // Maplibre order: top-left, top-right, bottom-right, bottom left

    if (coords.length === 5) coords = coords.slice(0, 4);

    // project into screen space
    const points = coords.map(([lng, lat]) => {
      const p = map.project([lng, lat]);
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

  function getExtentWkt(map: maplibre.Map): string {
    const bounds = map.getBounds();
    const zoom = map.getZoom();

    const bbox: BBox = [
      bounds.getWest(),
      bounds.getSouth(),
      bounds.getEast(),
      bounds.getNorth(),
    ];

    const decimals = decimalsForZoom(zoom);

    return bboxToWkt(bbox, decimals);
  }

  function getBounds(
    coordinates: GeoJSON.Position[],
  ): maplibre.LngLatBoundsLike {
    const lats = coordinates.map((c) => c[1]);
    const lngs = coordinates.map((c) => c[0]);
    const bounds = [
      [Math.min(...lngs), Math.min(...lats)],
      [Math.max(...lngs), Math.max(...lats)],
    ];
    return bounds as maplibre.LngLatBoundsLike;
  }

  function searchCurrentExtent() {
    if (!map || !onSearchExtent) return;

    const polygonWkt = getExtentWkt(map);
    onSearchExtent(polygonWkt);
  }

  function attachMap(element: HTMLElement) {
    //const initialState = { lng: 0.0, lat: 0.0, zoom: 10 };

    map = new maplibre.Map({
      container: element,
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
      mapLoaded = true;

      if (extent) {
        const bounds = getBounds(extent.coordinates[0]);
        map.fitBounds(bounds, { padding: 40 });
      }
    });

    resizeObserver = new ResizeObserver(() => {
      if (map) map.resize();
    });
    resizeObserver.observe(element);

    return () => {
      resizeObserver?.disconnect();
      map.remove();
    };
  }

  $effect(() => {
    if (!map || !mapLoaded || !imagePreview) return;

    const orderedCoords = reorderFootprint(imagePreview.coordinates, map);
    const url = `/thumbnails/${imagePreview.filename}.png`;

    const imageSource = map.getSource("image-preview") as
      | maplibre.ImageSource
      | undefined;

    if (imageSource !== undefined) {
      imageSource.updateImage({
        url: url,
        coordinates: orderedCoords,
      });
    } else {
      map.addSource("image-preview", {
        type: "image",
        url: url,
        coordinates: orderedCoords,
      });

      map.addLayer({
        id: "image-preview",
        type: "raster",
        source: "image-preview",
      });
    }

    const footprintSource = map.getSource("footprint") as
      | maplibre.GeoJSONSource
      | undefined;

    if (footprintSource !== undefined) {
      footprintSource.setData({
        type: "Polygon",
        coordinates: [imagePreview.coordinates],
      });
    } else {
      map.addSource("footprint", {
        type: "geojson",
        data: {
          type: "Polygon",
          coordinates: [imagePreview.coordinates],
        },
      });

      map.addLayer({
        id: "footprint",
        type: "line",
        source: "footprint",
        paint: {
          "line-color": "#f4320b",
          "line-width": 3,
        },
      });
    }

    const bounds = getBounds(imagePreview.coordinates);
    map.fitBounds(bounds, {
      padding: 40,
      bearing: imagePreview.azimuth_angle,
      pitch: imagePreview.look_angle,
      animate: true,
      duration: 500,
    });
  });
</script>

<div class="map" {@attach attachMap}>
  {#if showSearchButton}
    <button class="search-extent" onclick={searchCurrentExtent}>
      Search extent
    </button>
  {/if}
</div>

<style>
  .map {
    position: relative;
    width: 100%;
    height: 100%;
  }
  .search-extent {
    position: absolute;
    bottom: 1rem;
    left: 1rem;
    z-index: 1;
  }
</style>
