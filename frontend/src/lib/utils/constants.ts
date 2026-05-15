import * as v from "valibot";

export const ORDERING_OPTIONS = [
  { label: "Ascending", value: "asc" },
  { label: "Descending", value: "desc" },
] as const;

export const orderingSchema = v.picklist(ORDERING_OPTIONS.map((o) => o.value));

export const ORDER_COLUMN_OPTIONS = [
  {
    label: "Datetime collected",
    value: "datetime_collected",
  },
  { label: "Coverage", value: "coverage" },
  { label: "IIRS", value: "interpretation_rating" },
  {
    label: "GSD",
    value: "ground_sample_distance",
  },
  { label: "Azimuth angle", value: "azimuth_angle" },
  { label: "Look angle", value: "look_angle" },
] as const;

export const imageOrderColumnSchema = v.picklist(
  ORDER_COLUMN_OPTIONS.map((o) => o.value),
);
