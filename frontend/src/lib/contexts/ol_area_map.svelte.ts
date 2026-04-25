import { setContext, getContext } from "svelte";
import Feature from "ol/feature";
import Map from "ol/Map.js";
import TileLayer from "ol/layer/Tile.js";
import VectorLayer from "ol/layer/Vector";
import View from "ol/View.js";
import { Draw, Modify, defaults } from "ol/interaction";
import VectorSource from "ol/source/Vector";
import { Polygon } from "ol/geom";
import { Fill, Stroke, Style } from "ol/style";
import GeoJSON from "ol/format/GeoJSON";

import type { AreaEditorState } from "$lib/contexts/area_editor.svelte";
import { vertexStyle } from "$lib/utils/ol_styles";
import type { BBox } from "$lib/utils/geo/bbox";
import { transformExtent } from "ol/proj";
import { buildOlLayers, type LayerInfo } from "$lib/utils/map/layers";

export class AreaMapState {
  #map: Map | null = null;
  #baseLayers: TileLayer[] = $state([]);
  #polygonSource = new VectorSource();
  #drawInteraction: Draw | null = null;
  #initialExtent: BBox | null = null;

  public get layers(): LayerInfo[] {
    return this.#baseLayers.map((layer) => ({
      id: layer.get("id"),
      label: layer.get("label"),
      visible: layer.getVisible(),
    }));
  }

  constructor(polygons: GeoJSON.Polygon[] = [], initialBbox?: BBox | null) {
    this.#initialExtent = initialBbox ?? null;

    if (!polygons.length) return;
    const format = new GeoJSON();
    const features = polygons.map((polygon) => {
      return format.readFeature(polygon, {
        dataProjection: "EPSG:4326",
        featureProjection: "EPSG:3857",
      }) as Feature;
    });

    this.#polygonSource.addFeatures(features);
  }

  private destroy() {
    this.#map?.setTarget(undefined);
    this.#map?.getLayers().clear();
    this.#map?.dispose();
  }

  private async initMap(target: HTMLElement) {
    const response = await fetch("/map_config.json");
    const mapConfig = await response.json();
    const baseLayers = buildOlLayers(mapConfig.layers);
    this.#baseLayers = baseLayers;

    const polygonLayer = new VectorLayer({
      source: this.#polygonSource,
      style: [
        new Style({
          stroke: new Stroke({ color: "#3399CC", width: 2 }),
          fill: new Fill({ color: "rgba(255,255,255,0.2)" }),
        }),
        vertexStyle,
      ],
    });

    const mapView = new View({
      projection: "EPSG:3857",
      center: [0, 0],
      zoom: 2,
    });

    this.#map = new Map({
      target: target,
      controls: [],
      layers: [...baseLayers, polygonLayer],
      view: mapView,
      interactions: defaults({
        doubleClickZoom: false,
      }),
    });

    const modify = new Modify({
      source: this.#polygonSource,
    });
    this.#map.addInteraction(modify);

    if (!this.#polygonSource.isEmpty()) {
      mapView.fit(this.#polygonSource.getExtent(), {
        padding: [40, 40, 40, 40],
      });
    } else if (this.#initialExtent) {
      const extent = transformExtent(
        this.#initialExtent,
        "EPSG:4326",
        "EPSG:3857",
      );
      mapView.fit(extent, { padding: [40, 40, 40, 40] });
    }
  }

  private createDrawInteraction(areaEditorState: AreaEditorState) {
    const draw = new Draw({
      source: this.#polygonSource,
      type: "Polygon",
    });

    draw.on("drawend", (e) => {
      const feature = e.feature;
      const geometry = feature.getGeometry();

      if (geometry?.getType() === "Polygon") {
        const geometry4326 = geometry
          .clone()
          .transform("EPSG:3857", "EPSG:4326") as Polygon;

        areaEditorState.setGeometry(geometry4326);
      }

      if (this.#drawInteraction) {
        this.#map?.removeInteraction(this.#drawInteraction);
        this.#drawInteraction = null;
      }
    });
    return draw;
  }

  public attach(target: HTMLElement) {
    if (this.#map) return;

    this.initMap(target);

    return () => {
      this.destroy();
    };
  }

  public updateDrawInteraction(areaEditorState: AreaEditorState) {
    if (!this.#map) return;

    if (this.#drawInteraction) {
      this.#map.removeInteraction(this.#drawInteraction);
      this.#drawInteraction = null;
      return;
    }

    if (!areaEditorState.drawMode) return;

    this.#polygonSource.clear();

    const draw = this.createDrawInteraction(areaEditorState);
    this.#drawInteraction = draw;
    this.#map.addInteraction(draw);
  }

  public selectLayer(id: string) {
    for (const layer of this.#baseLayers) {
      layer.setVisible(layer.get("id") === id);
    }
  }
}

const AREAMAP_KEY = Symbol("IMAGEVIEWER");

export function setAreaMapState(
  polygons: GeoJSON.Polygon[] = [],
  initialBbox?: BBox | null,
) {
  const state = new AreaMapState(polygons, initialBbox);
  return setContext(AREAMAP_KEY, state);
}

export function getAreaMapState() {
  const context = getContext<ReturnType<typeof setAreaMapState>>(AREAMAP_KEY);
  if (!context) {
    throw new Error("getAreaMapState must be used within a provider");
  }
  return context;
}
