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
