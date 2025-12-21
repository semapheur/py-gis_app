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
