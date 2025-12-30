import { getContext, setContext } from "svelte";

export const annotateTabs = [
  { name: "Equipment", value: "equipment" },
  { name: "Activity", value: "activity" },
] as const;
export type AnnotateForm = (typeof annotateTabs)[number]["value"];

export const annotateGeometryByForm = {
  equipment: [
    { label: "Point", value: "Point" },
    { label: "Polygon", value: "Polygon" },
  ],
  activity: [
    { label: "Polygon", value: "Polygon" },
    { label: "MultiPolygon", value: "MultiPolygon" },
  ],
} as const;

type AnnotateGeometryOptions = typeof annotateGeometryByForm;
export type AnnotateGeometry<F extends keyof AnnotateGeometryOptions> =
  AnnotateGeometryOptions[F][number]["value"];

export interface EquipmentData {
  id: string | null;
  confidence: EquipmentConfidence;
  status: EquipmentStatus;
}

export const equipmentConfidence = ["High", "Medium", "Low"] as const;
export type EquipmentConfidence = Lowercase<
  (typeof equipmentConfidence)[number]
>;
export const equipmentStatus = ["Intact", "Damaged", "Destroyed"] as const;
export type EquipmentStatus = Lowercase<(typeof equipmentStatus)[number]>;

export interface ActivityData {
  type: string;
}

export interface AnnotateConfig {
  active: boolean;
  layer: AnnotateForm;
  geometry: AnnotateGeometry<AnnotateForm>;
  data: EquipmentData | ActivityData;
}

const defaultLayer = "equipment";

export class AnnotateState {
  #config = $state<AnnotateConfig>({
    active: false,
    layer: defaultLayer,
    geometry: annotateGeometryByForm[defaultLayer][0].value,
    data: this.createDefaultData(defaultLayer),
  });

  label = $derived.by(() => {
    const { layer, data } = this.#config;
    if (!data) return "";

    if (layer === "equipment") {
      const d = data as EquipmentData;
      return `${d.id}\n${d.confidence}\n${d.status}`;
    }

    if (layer === "activity") {
      const d = data as ActivityData;
      return `${d.type}`;
    }
    return "";
  });

  validData = $derived.by(() => {
    const { layer, data } = this.#config;

    if (layer === "equipment") {
      const d = data as EquipmentData;
      return !!d?.id;
    }

    if (layer === "activity") {
      const d = data as ActivityData;
      return !!d?.type;
    }

    return false;
  });

  geometryOptions = $derived(annotateGeometryByForm[this.#config.layer]);

  constructor() {}

  private createDefaultData(layer: AnnotateForm) {
    if (layer === "equipment") {
      return {
        id: null,
        confidence: equipmentConfidence[0].toLowerCase() as EquipmentConfidence,
        status: equipmentStatus[0].toLowerCase() as EquipmentStatus,
      } satisfies EquipmentData;
    }

    if (layer === "activity") {
      return {
        type: "deployment",
      };
    }
  }

  get active() {
    return this.#config.active;
  }
  get layer() {
    return this.#config.layer;
  }
  get geometry() {
    return this.#config.geometry;
  }
  get data() {
    return this.#config.data;
  }

  setLayer(layer: AnnotateForm) {
    if (this.layer === layer) return;

    this.#config.layer = layer;
    this.#config.geometry = annotateGeometryByForm[layer][0].value;
    this.#config.data = this.createDefaultData(layer);
  }

  setGeometry(value: AnnotateGeometry<AnnotateForm>) {
    this.#config.geometry = value;
  }

  setData(data: EquipmentData | ActivityData) {
    this.#config.data = data;
  }

  toggleActive() {
    if (!this.validData) return;
    this.#config.active = !this.#config.active;
  }

  stop() {
    this.#config.active = false;
  }
}

const ANNOTATE_KEY = Symbol("ANNOTATE");

export function setAnnotateState() {
  const state = new AnnotateState();
  return setContext(ANNOTATE_KEY, state);
}

export function getAnnotateState() {
  const context = getContext<ReturnType<typeof setAnnotateState>>(ANNOTATE_KEY);
  if (!context) {
    throw new Error("getAnnotateContext must be used within a provider");
  }
  return context;
}
