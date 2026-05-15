import { error } from "@sveltejs/kit";
import { encode, decode } from "@msgpack/msgpack";
import * as v from "valibot";
import type { PageLoad } from "./$types";
import type { ImageMetadata } from "$lib/utils/types";
import { parseToUnix } from "$lib/utils/date";
import { ORDERING_OPTIONS, ORDER_COLUMN_OPTIONS } from "$lib/utils/constants";

export const prerender = false;

interface ImageSearchResult {
  wkt: string | null;
  images: ImageMetadata[];
}

const dateField = v.nullish(
  v.pipe(
    v.string(),
    v.regex(/^\d{4}-\d{2}-\d{2}$/, "Expected YYYY-MM-DD"),
    v.transform(parseToUnix),
  ),
);

const azimuthField = v.nullish(
  v.pipe(
    v.string(),
    v.transform(Number),
    v.finite(),
    v.minValue(0),
    v.maxValue(359),
  ),
);

const searchSchema = v.pipe(
  v.object({
    wkt: v.nullish(v.string()),
    area_id: v.nullish(
      v.pipe(v.string(), v.uuid("area_id must be a valid UUID")),
    ),
    ordering: v.picklist(ORDERING_OPTIONS.map((o) => o.value)),
    order_by: v.picklist(ORDER_COLUMN_OPTIONS.map((o) => o.value)),
    filename: v.nullish(v.string()),
    min_coverage: v.nullish(
      v.pipe(
        v.string(),
        v.transform(Number),
        v.finite(),
        v.minValue(0),
        v.maxValue(100),
      ),
    ),
    min_iirs: v.nullish(
      v.pipe(
        v.string(),
        v.transform(Number),
        v.finite(),
        v.minValue(0),
        v.maxValue(9),
      ),
    ),
    max_gsd: v.nullish(
      v.pipe(v.string(), v.transform(Number), v.finite(), v.minValue(0)),
    ),
    date_start: dateField,
    date_end: dateField,
    azimuth_start: azimuthField,
    azimuth_end: azimuthField,
  }),

  v.check(
    (p) => (p.date_start === null) === (p.date_end === null),
    "date_start and date_end must both be provided or both emitted",
  ),

  v.check(
    (d) =>
      !d.date_start ||
      !d.date_end ||
      new Date(d.date_start) <= new Date(d.date_end),
    "date_start must be before or equal to date_end",
  ),

  v.check(
    (p) => (p.azimuth_start === null) === (p.azimuth_end === null),
    "azimuth_start and azimuth_end must both be provided or both emitted",
  ),
);

export const load: PageLoad = async ({ fetch, url }) => {
  const raw = {
    wkt: url.searchParams.get("wkt"),
    area_id: url.searchParams.get("area"),
    ordering: url.searchParams.get("ordering"),
    order_by: url.searchParams.get("order_by"),
    filename: url.searchParams.get("filename"),
    min_coverage: url.searchParams.get("min_coverage"),
    min_iirs: url.searchParams.get("min_iirs"),
    max_gsd: url.searchParams.get("max_gsd"),
    date_start: url.searchParams.get("date_start"),
    date_end: url.searchParams.get("date_end"),
    azimuth_start: url.searchParams.get("azimuth_start"),
    azimuth_end: url.searchParams.get("azimuth_end"),
  };

  const result = v.safeParse(searchSchema, raw);

  if (!result.success) {
    const messages = v.flatten(result.issues);
    const fieldErrors = Object.entries(messages.nested ?? {})
      .map(([field, errors]) => `${field}: ${errors?.join(", ")}`)
      .join("; ");
    const rootErrors = messages.root?.join("; ") ?? "";
    throw error(
      400,
      `Invalid search parameters: ${[rootErrors, fieldErrors].filter(Boolean).join("; ")}`,
    );
  }

  const response = await fetch("/api/search-images", {
    method: "POST",
    headers: { "Content-Type": "application/msgpack" },
    body: encode(result.output),
  });

  if (!response.ok) {
    throw error(response.status, "Failed to fetch images");
  }

  return decode(await response.arrayBuffer()) as ImageSearchResult;
};
