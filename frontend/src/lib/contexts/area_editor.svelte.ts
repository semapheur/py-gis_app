import { getContext, setContext } from "svelte";
import type { Polygon } from "ol/geom";
import WKT from "ol/format/WKT";

interface AreaData {
  name: string | null;
  description: string | null;
  geometry: Polygon | null;
}

export class AreaEditorState {
  drawMode = $state<boolean>(false);
  data = $state<AreaData>({
    name: null,
    description: null,
    geometry: null,
  });

  get hasPolygon() {
    return this.data.geometry !== null;
  }

  public setGeometry(geometry: Polygon) {
    this.data.geometry = geometry;
    this.drawMode = false;
  }

  public toggleDraw() {
    if (this.data.geometry) {
      this.data.geometry = null;
      this.drawMode = true;
      return;
    }

    this.drawMode = !this.drawMode;
  }

  public valid() {
    const data = this.data;

    return Boolean(data.name && data.geometry);
  }

  public async persist() {
    if (!this.valid()) return;

    const format = new WKT();

    const payload = {
      id: crypto.randomUUID(),
      name: this.data.name,
      description: this.data.description,
      geometry: format.writeGeometry(this.data!.geometry),
      createdByUserId: "",
      createdAtTimestamp: Date.now(),
    };

    const response = await fetch("/api/update-area", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const error = await response.json();
    }
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
