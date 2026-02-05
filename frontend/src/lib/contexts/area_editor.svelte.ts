import { getContext, setContext } from "svelte";
import type { Polygon } from "ol/geom";

export class AreaEditorState {
  #drawMode = $state<boolean>(false);
  #geometry = $state<Polygon | null>(null);

  get drawMode() {
    return this.#drawMode;
  }

  get hasPolygon() {
    return this.#geometry != null;
  }

  public setGeometry(geometry: Polygon) {
    this.#geometry = geometry;
    this.#drawMode = false;
  }

  public toggleDraw() {
    if (this.#geometry) {
      this.#geometry = null;
      this.#drawMode = true;
      return;
    }

    this.#drawMode = !this.#drawMode;
  }
}

const AREAEDITOR_KEY = Symbol("AREAEDITOR");

export function setAreaEditorState() {
  const state = new AreaEditorState();
  return setContext(AREAEDITOR_KEY, state);
}

export function getAreaEditorState() {
  const context =
    getContext<ReturnType<typeof setAreaEditorState>>(AREAEDITOR_KEY);
  if (!context) {
    throw new Error("getAreaEditorState must be used within a provider");
  }
  return context;
}
