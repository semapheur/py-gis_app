export interface BandStatistics {
  data_type: string;
  color_interpretation: string;
  min: number;
  max: number;
  mean: number;
  stddev: number;
}

export interface ImageInfo {
  id: string;
  filename: string;
  datetime_collected: number;
  classification: string;
  image_type: "grd" | "pan" | "ms" | "slc";
  band_statistics: BandStatistics[];
}

export interface ImageMetadata extends ImageInfo {
  catalog: number;
  relative_path: string;
  filetype: string;
  datetime_collected: number;
  sensor_name: string;
  sensor_type: "eo" | "sar";
  footprint: GeoJSON.Polygon;
  look_angle: number;
  azimuth_angle: number;
  ground_sample_distance_row: number;
  ground_sample_distance_col: number;
  interpretation_rating: number;
  coverage: number;
}

export interface ImagePreviewInfo {
  filename: string;
  polygon: GeoJSON.Polygon;
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

export interface AttributeTableInfo {
  name: string;
  label: string;
}

export interface AngleRange {
  start: number;
  end: number;
}
