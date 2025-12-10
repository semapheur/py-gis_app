export interface ImageMetadata {
  directory: string;
  filename: string;
  filetype: string;
  classification: string;
  datetime_collected: string;
  sensor_name: string;
  sensor_type: string;
  footprint: GeoJSON.Polygon; // WKT
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
