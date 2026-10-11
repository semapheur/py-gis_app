import { parseToUnix } from "#lib/utils/date.ts";
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

const numberField = (min: number, max = Infinity) =>
  v.nullish(
    v.pipe(
      v.string(),
      v.transform(Number),
      v.finite(),
      v.minValue(min),
      v.maxValue(max),
    ),
  );

const dateField = v.nullish(
  v.pipe(
    v.string(),
    v.regex(/^\d{4}-\d{2}-\d{2}$/, "Expected YYYY-MM-DD"),
    v.transform(parseToUnix),
  ),
);

export const searchSchema = v.pipe(
  v.object({
    wkt: v.nullish(v.string()),
    area_id: v.nullish(
      v.pipe(v.string(), v.uuid("area_id must be a valid UUID")),
    ),
    ordering: v.nullish(v.picklist(ORDERING_OPTIONS.map((o) => o.value))),
    order_by: v.nullish(v.picklist(ORDER_COLUMN_OPTIONS.map((o) => o.value))),
    filename: v.nullish(v.string()),
    min_coverage: numberField(0, 100),
    min_iirs: numberField(0, 9),
    max_gsd: numberField(0),
    date_start: dateField,
    date_end: dateField,
    azimuth_start: numberField(0, 359),
    azimuth_end: numberField(0, 359),
    lookangle_min: numberField(0, 90),
    lookangle_max: numberField(0, 90),
  }),

  v.forward(
    v.check(
      (p) => (p.date_start == null) === (p.date_end == null),
      "date_start and date_end must be provided together",
    ),
    ["date_end"],
  ),
  v.forward(
    v.check(
      (p) =>
        p.date_start == null ||
        p.date_end == null ||
        p.date_start <= p.date_end,
      "date_start must not be after date_end",
    ),
    ["date_end"],
  ),
  v.forward(
    v.check(
      (p) => (p.azimuth_start == null) === (p.azimuth_end == null),
      "azimuth_start and azimuth_end must be provided together",
    ),
    ["azimuth_end"],
  ),
  v.forward(
    v.check(
      (p) =>
        p.lookangle_min == null ||
        p.lookangle_max == null ||
        p.lookangle_min <= p.lookangle_max,
      "lookangle_min must be less than or equal to lookangle_max",
    ),
    ["lookangle_max"],
  ),
);
