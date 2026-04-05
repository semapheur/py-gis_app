export interface ImageStats {}

export interface ImageInfo {
  id: string;
  filename: string;
  classification: string;
  image_type: "grd" | "pan" | "ms" | "slc";
}

export interface ImageMetadata extends ImageInfo {
  catalog: number;
  relative_path: string;
  filetype: string;
  datetime_collected: number;
  sensor_name: string;
  sensor_type: "eo" | "sar";
  footprint?: GeoJSON.Polygon; // WKT
  look_angle: number;
  azimuth_angle: number;
  ground_sample_distance_row: number;
  ground_sample_distance_col: number;
  interpretation_rating: number;
  coverage: number;
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

export interface SelectOption<T = string> {
  label: string;
  value: T;
}
