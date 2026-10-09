import type { AttributeValue, NonNull } from "#lib/utils/types.js";
import { isSet } from "#lib/utils/validation.js";

export interface PersonnelPointData {
  confidence: AttributeValue | null;
  affiliation: AttributeValue | null;
}

export interface PersonnelPolygonData extends PersonnelPointData {
  min_count: number | null;
  max_count: number | null;
}

export type ValidPersonnelPointData = NonNull<PersonnelPointData>;
export type ValidPersonnelPolygonData = NonNull<PersonnelPolygonData>;
export type PersonnelData = PersonnelPointData | PersonnelPolygonData;
export type PersonnelPatch = Partial<PersonnelPointData & PersonnelPolygonData>;
export type PersonnelTableData = ValidPersonnelPointData & PersonnelPolygonData;

interface PersonnelSingleDef {
  kind: "single";
  label: string;
  table: string;
  required?: boolean;
  column?: boolean;
}
interface PersonnelNumberDef {
  kind: "number";
  label: string;
  column?: boolean;
}
type PersonnelFieldDef = PersonnelSingleDef | PersonnelNumberDef;

export const personnelSchema = {
  confidence: {
    kind: "single",
    label: "Confidence",
    table: "equipment_confidence", // adjust to your table names
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
  min_count: { kind: "number", label: "Min count", column: true },
  max_count: { kind: "number", label: "Max count", column: true },
} as const satisfies Record<string, PersonnelFieldDef>;

export type PersonnelFieldKey = keyof typeof personnelSchema;

export const personnelColumnFields = (
  Object.entries(personnelSchema) as [PersonnelFieldKey, PersonnelFieldDef][]
).filter(([, def]) => def.column);

export function personnelDisplayRow(
  data: PersonnelTableData,
): Record<string, unknown> {
  const row: Record<string, unknown> = {};

  for (const [key, def] of personnelColumnFields) {
    const value = data[key];

    if (def.kind === "single") {
      row[key] = (value as AttributeValue | null)?.label ?? "";
    } else if (def.kind === "number") {
      // numeric
      row[key] = value ?? null;
    }
  }

  return row;
}

export function createDefaultPersonnelData(
  geometry: GeoJSON.GeoJsonGeometryTypes,
) {
  if (geometry === "Point") {
    return {
      confidence: null,
      affiliation: null,
    } satisfies PersonnelPointData;
  }

  if (geometry === "Polygon") {
    return {
      min_count: null,
      max_count: null,
      confidence: null,
      affiliation: null,
    } satisfies PersonnelPolygonData;
  }

  return;
}

export function isPersonnelValid(
  data: PersonnelData | undefined,
  geometry: GeoJSON.GeoJsonGeometryTypes,
) {
  if (!data) return false;

  if (geometry === "Point") {
    const p = data as PersonnelPointData;
    return isSet(p.affiliation) && isSet(p.confidence);
  }

  if (geometry === "Polygon") {
    const p = data as PersonnelPolygonData;
    return (
      isSet(p.affiliation) &&
      isSet(p.confidence) &&
      Number.isInteger(p.min_count) &&
      Number.isInteger(p.max_count) &&
      p.min_count >= 0 &&
      p.min_count <= p.max_count
    );
  }

  return false;
}

export function serializePersonnelData(data: PersonnelData) {
  return {
    affiliation: data.affiliation?.id ?? null,
    confidence: data.confidence?.id ?? null,
    min_count: "min_count" in data ? data.min_count : null,
    max_count: "max_count" in data ? data.max_count : null,
  };
}
