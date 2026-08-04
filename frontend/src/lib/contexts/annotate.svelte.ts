import {
  createDefaultEquipmentData,
  equipmentRequiredFields,
  type EquipmentData,
} from "$lib/schemas/equipment_annotation";
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

type MultiAttributeField = "modification" | "camoflage" | "alternatives";
type NumericField = "heading" | "speed";

export type ValidEquipmentData = {
  [
    K in keyof EquipmentData as Exclude<K, MultiAttributeField | NumericField>
  ]-?: NonNullable<EquipmentData[K]>;
} & Pick<EquipmentData, MultiAttributeField | NumericField>;

interface AttributeMetaData {
  createdByUserId: string;
  createdAtTimestamp: number;
  modifiedByUserId: string;
  modifiedAtTimestamp: number;
}

export interface AnnotationBaseInfo {
  id: string;
  geometry: GeoJSON.Point | GeoJSON.Polygon;
  label: string;
  data: EquipmentData;
}

export interface AnnotationInfo extends AnnotationBaseInfo {
  metaData: AttributeMetaData;
}

export interface GhostCollection {
  image_id: string;
  datetime: number;
  annotations: AnnotationBaseInfo[];
}

export const activityTypes = ["Maneuver"] as const;
export type ActivityType = Lowercase<(typeof activityTypes)[number]>;

const defaultLayer = "equipment";

export class AnnotateState {
  layer = $state<AnnotateForm>(defaultLayer);
  geometry = $state<AnnotateGeometry<AnnotateForm>>(
    annotateGeometryByForm[defaultLayer][0].value,
  );
  data = $state<EquipmentData | ActivityData>(
    this.#createDefaultData(defaultLayer),
  );

  value = $derived.by(() => {
    if (this.layer === "equipment") {
      const d = this.data as EquipmentData;
      return {
        equipment: d.equipment?.id,
        confidence: d.confidence?.id,
        status: d.status?.id,
      };
    }
  });

  label = $derived.by(() => {
    if (this.layer === "equipment") {
      const d = this.data as ValidEquipmentData;
      return `${d.equipment.label}\n${d.confidence.label}`;
    }

    if (this.layer === "activity") {
      const d = this.data as ActivityData;
      return `${d.type}`;
    }
    return "";
  });

  isValid = $derived.by(() => {
    if (this.layer === "equipment") {
      const d = this.data as EquipmentData;
      return equipmentRequiredFields.every((field) => d[field] != null);
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
    this.data = this.#createDefaultData(layer);
  }

  setGeometry(value: AnnotateGeometry<AnnotateForm>) {
    this.geometry = value;
  }

  setData(data: EquipmentData | ActivityData) {
    this.data = data;
  }

  #createDefaultData(layer: AnnotateForm) {
    if (layer === "equipment") {
      return createDefaultEquipmentData();
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
