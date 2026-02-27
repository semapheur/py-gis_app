import { getContext, setContext } from "svelte";

export const measureOptions = ["Area", "Length"] as const;
export type MeasurementType = Lowercase<(typeof measureOptions)[number]>;

export type InteractionMode = "draw" | "edit";
export type InteractionSet = "annotation" | "measurement";

export class ImageViewerState {
  activeSet = $state<InteractionSet>("annotation");
  activeMode = $state<InteractionMode>("edit");

  public setActiveSet(set: InteractionSet) {
    this.activeSet = set;
  }

  public setActiveMode(mode: InteractionMode) {
    this.activeMode = mode;
  }
}

const VIEWER_STATE_KEY = Symbol("VIEWER_STATE");
export function setImageViewerState() {
  const context = new ImageViewerState();

  setContext(VIEWER_STATE_KEY, context);
  return context;
}

export function getImageViewerState() {
  return getContext<ImageViewerState>(VIEWER_STATE_KEY);
}
