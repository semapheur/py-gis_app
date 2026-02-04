import { getContext, setContext } from "svelte";

export class AreaEditorState {
  drawMode = $state<boolean>(false);

  public toggleDraw() {
    this.drawMode = !this.drawMode;
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
