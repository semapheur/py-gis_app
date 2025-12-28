export interface ImageStats {}

export interface ImageMetadata {
  id?: string;
  catalog: number;
  relative_path: string;
  filename: string;
  filetype: string;
  classification: string;
  datetime_collected: string;
  sensor_name: string;
  sensor_type: "eo" | "sar";
  image_type: "grd" | "pan" | "ms" | "slc";
  footprint?: GeoJSON.Polygon; // WKT
  look_angle: number;
  azimuth_angle: number;
  ground_sample_distance_row: number;
  ground_sample_distance_col: number;
  interpretation_rating: number;
  coverage?: number;
}

export interface ImagePreviewInfo {
  filename: string;
  coordinates: GeoJSON.Position[];
  azimuth_angle: number;
  look_angle: number;
}

export interface NoiseParams {
  type: "ABSOLUTE" | "RELATIVE";
  poly: number[][];
}

export interface RadiometricParams {
  noise: NoiseParams;
  sigma0: number[][];
}

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

export interface DrawConfig {
  enabled: boolean;
  layer: AnnotateForm;
  geometry: AnnotateGeometry<AnnotateForm>;
}
