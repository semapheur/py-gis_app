import type { AttributeValue, UnitOption } from "$lib/utils/types";

export const speedUnits = [
  { label: "km/h", value: "kmph", factor: 1 / 3.6 },
  { label: "m/s", value: "mps", factor: 1 },
  { label: "kt", value: "kt", factor: 1852 / 3600 },
] satisfies UnitOption[];

export const angleUnits = [
  { label: "deg", value: "deg", factor: 1 },
  { label: "mil", value: "mil", factor: 0.05625 },
] satisfies UnitOption[];

interface SelectFieldDef {
  kind: "search" | "multi-search" | "single" | "multi";
  label: string;
  table?: string;
  required?: boolean;
  column?: boolean;
}

interface NumericFieldDef {
  kind: "numeric";
  label: string;
  units: UnitOption[];
  min?: string;
  column?: boolean;
  backendKey?: string;
}

type FieldDef = SelectFieldDef | NumericFieldDef;

export const equipmentSchema = {
  equipment: {
    kind: "search",
    label: "Equipment",
    required: true,
    column: true,
  },
  confidence: {
    kind: "single",
    label: "Confidence",
    table: "equipment_confidence",
    required: true,
    column: true,
  },
  status: {
    kind: "single",
    label: "Status",
    table: "equipment_status",
    required: true,
    column: true,
  },
  affiliation: {
    kind: "single",
    label: "Affiliation",
    table: "equipment_affiliation",
    required: true,
    column: true,
  },
  visibility: {
    kind: "single",
    label: "Visibility",
    table: "equipment_visibility",
    required: true,
    column: true,
  },
  configuration: {
    kind: "single",
    label: "Configuration",
    table: "equipment_configuration",
    required: true,
    column: true,
  },
  modification: {
    kind: "multi",
    label: "Modification",
    table: "equipment_modification",
    column: true,
  },
  camoflage: {
    kind: "multi",
    label: "Camoflage",
    table: "equipment_camoflage",
    column: true,
  },
  alternatives: {
    kind: "multi-search",
    label: "Alternatives",
    column: true,
  },
  heading: {
    kind: "numeric",
    label: "Heading",
    units: angleUnits,
    column: true,
    backendKey: "heading_deg",
  },
  elevation: {
      kind: "numeric",
      label: "Elevation",
      units: angleUnits,
      column: true,
      backendKey: "elevation_deg",
    },,
  speed: {
    kind: "numeric",
    label: "Speed",
    units: speedUnits,
    min: "0",
    column: true,
    backendKey: "speed_mps",
  },
} as const satisfies Record<string, FieldDef>;

export type EquipmentFieldKey = keyof typeof equipmentSchema;
export type EquipmentFieldDef = (typeof equipmentSchema)[EquipmentFieldKey];

type ValueForKind<K extends EquipmentFieldDef["kind"]> = K extends "multi"
  ? AttributeValue[] | null
  : K extends "numeric"
    ? number | null
    : AttributeValue | null;

export type EquipmentData = {
  [K in EquipmentFieldKey]: ValueForKind<(typeof equipmentSchema)[K]["kind"]>;
};

export const equipmentRequiredFields = (
  Object.entries(equipmentSchema) as [EquipmentFieldKey, EquipmentFieldDef][]
)
  .filter(([, def]) => def.required)
  .map(([key]) => key);

export function createDefaultEquipmentData(): EquipmentData {
  return Object.fromEntries(
    Object.keys(equipmentSchema).map((k) => [k, null]),
  ) as EquipmentData;
}

export const equipmentAttributeTables = Object.fromEntries(
  (Object.entries(equipmentSchema) as [EquipmentFieldKey, EquipmentFieldDef][])
    .filter(([, def]) => "table" in def)
    .map(([key, def]) => [key, (def as { table: string }).table]),
) as Record<string, string>;

export type EquipmentAttributeName = keyof typeof equipmentAttributeTables;

export const equipmentColumnFields = (
  Object.entries(equipmentSchema) as [EquipmentFieldKey, EquipmentFieldKey][]
).filter(([, def]) => def.column);

export function equipmentDisplayRow(
  data: ValidEquipmentData,
): Record<string, unknown> {
  const row: Record<string, unknown> = {};

  for (const [key, def] of equipmentColumnFields) {
    const value = data[key];

    if (def.kind === "multi" || def.kind === "multi-search") {
      row[key] = (value as AnnotateValue[] | null)?.map((v) => v.label) ?? [];
    } else if (def.kind === "single" || def.kind === "search") {
      row[key] = (value as AnnotateValue | null)?.label ?? "";
    } else {
      // numeric
      row[key] = value ?? null;
    }
  }

  return row;
}

export function serializeEquipmentData(
  data: EquipmentData,
): Record<string, unknown> {
  const out: Record<string, unknown> = {};

  for (const [key, def] of Object.entries(equipmentSchema) as [
    EquipmentFieldKey,
    EquipmentFieldDef,
  ][]) {
    const wireKey = def?.backendKey ?? key;
    const value = data[key];

    if (def.kind === "multi" || def.kind === "multi-search") {
      out[wireKey] = (value as AttributeValue[] | null)?.map((v) => v.id) ?? [];
    } else if (def.kind === "single" || def.kind === "search") {
      out[wireKey] = (value as AttributeValue | null)?.id ?? null;
    } else {
      out[wireKey] = (value as number | null) ?? null;
    }
  }

  return out;
}
