import { setContext, getContext } from "svelte";
import Map from "ol/Map.js";
import TileLayer from "ol/layer/Tile.js";
import VectorLayer from "ol/layer/Vector";
import View from "ol/View.js";
import XYZ from "ol/source/XYZ";
import { Draw } from "ol/interaction";
import VectorSource from "ol/source/Vector";
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
    });
  }
  private createDrawInteraction() {
    const draw = new Draw({
      source: this.#polygonSource,
      type: "Polygon",
    });

    draw.on("drawend", (e) => {});
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
    }

    const draw = this.createDrawInteraction();

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
