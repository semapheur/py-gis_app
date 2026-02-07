import { setContext, getContext } from "svelte";
import Map from "ol/Map.js";
import TileLayer from "ol/layer/Tile.js";
import VectorLayer from "ol/layer/Vector";
import View from "ol/View.js";
import XYZ from "ol/source/XYZ";
import { Draw, defaults } from "ol/interaction";
import VectorSource from "ol/source/Vector";
import { Polygon } from "ol/geom";
import type { AreaEditorState } from "$lib/contexts/area_editor.svelte";

export class AreaMapState {
  #map: Map | null = null;
  #polygonSource = new VectorSource();
  #drawInteraction: Draw | null = null;

  private destroy() {
    this.#map?.setTarget(undefined);
    this.#map?.getLayers().clear();
    this.#map?.dispose();
  }

  private initMap(target: HTMLElement) {
    const mapLayer = new TileLayer({
      source: new XYZ({
        url: "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png",
      }),
    });

    const polygonLayer = new VectorLayer({
      source: this.#polygonSource,
    });

    const mapView = new View({
      projection: "EPSG:3857",
      center: [0, 0],
      zoom: 2,
    });

    this.#map = new Map({
      target: target,
      layers: [mapLayer, polygonLayer],
      view: mapView,
      interactions: defaults({
        doubleClickZoom: false,
      }),
    });
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
}

const AREAMAP_KEY = Symbol("IMAGEVIEWER");

export function setAreaMapState() {
  const state = new AreaMapState();
  return setContext(AREAMAP_KEY, state);
}

export function getAreaMapState() {
  const context = getContext<ReturnType<typeof setAreaMapState>>(AREAMAP_KEY);
  if (!context) {
    throw new Error("getAreaMapState must be used within a provider");
  }
  return context;
}
