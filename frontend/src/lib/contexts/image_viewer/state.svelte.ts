import { getContext, setContext } from "svelte";

export type InteractionMode = "draw" | "edit";
export type InteractionSet = "annotation" | "measurement";

export class ViewerState {
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
export function createViewerContext() {
  const context = new ViewerState();

  setContext(VIEWER_STATE_KEY, context);
  return context;
}

export function getViewerContext() {
  return getContext<ViewerState>(VIEWER_STATE_KEY);
}
