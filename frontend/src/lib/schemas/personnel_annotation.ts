import type { AttributeValue } from "$lib/utils/types";

export interface PersonnelPointData {
  confidence: AttributeValue | null;
  affiliation: AttributeValue | null;
}

export interface PersonnelPolygonData {
  min_count: number | null;
  max_count: number | null;
  affiliation: AttributeValue | null;
}

export type PersonnelData = PersonnelPointData | PersonnelPolygonData;

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
      affiliation: null,
    } satisfies PersonnelPolygonData;
  }

  return;
}
