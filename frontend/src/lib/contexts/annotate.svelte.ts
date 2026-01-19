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

export interface ActivityData {
  summary: string;
  type: string;
  observed: string;
  comment: string;
}

export const activityTypes = ["Maneuver"] as const;
export type ActivityType = Lowercase<(typeof activityTypes)[number]>;

export interface EquipmentData {
  id: string | null;
  confidence: string;
  status: string;
}

export const equipmentConfidence = ["High", "Medium", "Low"] as const;
export type EquipmentConfidence = Lowercase<
  (typeof equipmentConfidence)[number]
>;
export const equipmentStatus = ["Intact", "Damaged", "Destroyed"] as const;
export type EquipmentStatus = Lowercase<(typeof equipmentStatus)[number]>;

const defaultLayer = "equipment";

export class AnnotateState {
  active = $state<boolean>(false);
  layer = $state<AnnotateForm>(defaultLayer);
  geometry = $state<AnnotateGeometry<AnnotateForm>>(
    annotateGeometryByForm[defaultLayer][0].value,
  );
  data = $state<EquipmentData | ActivityData>(
    this.createDefaultData(defaultLayer),
  );

  label = $derived.by(() => {
    if (this.layer === "equipment") {
      const d = this.data as EquipmentData;
      return `${d.id}\n${d.confidence}\n${d.status}`;
    }

    if (this.layer === "activity") {
      const d = this.data as ActivityData;
      return `${d.type}`;
    }
    return "";
  });

  validData = $derived.by(() => {
    if (this.layer === "equipment") {
      const d = this.data as EquipmentData;
      return !!d?.id;
    }

    if (this.layer === "activity") {
      const d = this.data as ActivityData;
      return !!d?.type;
    }

    return false;
  });

  geometryOptions = $derived(annotateGeometryByForm[this.layer]);

  constructor() {}

  setLayer(layer: AnnotateForm) {
    if (this.layer === layer) return;

    this.layer = layer;
    this.geometry = annotateGeometryByForm[layer][0].value;
    this.data = this.createDefaultData(layer);
  }

  setGeometry(value: AnnotateGeometry<AnnotateForm>) {
    this.geometry = value;
  }

  setData(data: EquipmentData | ActivityData) {
    this.data = data;
  }

  toggleActive() {
    if (!this.validData) return;
    this.active = !this.active;
  }

  stop() {
    this.active = false;
  }

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
}

const ANNOTATE_KEY = Symbol("ANNOTATE");

export function setAnnotateState() {
  const state = new AnnotateState();
  return setContext(ANNOTATE_KEY, state);
}

export function getAnnotateState() {
  const context = getContext<ReturnType<typeof setAnnotateState>>(ANNOTATE_KEY);
  if (!context) {
    throw new Error("getAnnotateState must be used within a provider");
  }
  return context;
}
