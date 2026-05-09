import { error } from "@sveltejs/kit";
import * as v from "valibot";
import type { PageLoad } from "./$types";
import type { ImageMetadata } from "$lib/utils/types";
import { parseToUnix } from "$lib/utils/date";

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

const searchSchema = v.pipe(
  v.object({
    wkt: v.nullish(v.string()),
    area_id: v.nullish(
      v.pipe(v.string(), v.uuid("area_id must be a valid UUID")),
    ),
    filename: v.nullish(v.string()),
    min_coverage: v.nullish(
      v.pipe(
        v.string(),
        v.transform(Number),
        v.integer(),
        v.minValue(0),
        v.maxValue(100),
      ),
    ),
    min_iirs: v.nullish(
      v.pipe(v.string(), v.transform(Number), v.minValue(0), v.maxValue(9)),
    ),
    max_gsd: v.nullish(v.pipe(v.string(), v.transform(Number), v.minValue(0))),
    date_start: dateField,
    date_end: dateField,
  }),

  v.check(
    (d) => (d.date_start === null) === (d.date_end === null),
    "date_start and date_end must both be provided or both emitted",
  ),

  v.check(
    (d) =>
      !d.date_start ||
      !d.date_end ||
      new Date(d.date_start) <= new Date(d.date_end),
    "date_start must be before or equal to date_end",
  ),
);

export const load: PageLoad = async ({ fetch, url }) => {
  const raw = {
    wkt: url.searchParams.get("wkt"),
    area_id: url.searchParams.get("area"),
    filename: url.searchParams.get("filename"),
    min_coverage: url.searchParams.get("min_coverage"),
    min_iirs: url.searchParams.get("min_iirs"),
    max_gsd: url.searchParams.get("max_gsd"),
    date_start: url.searchParams.get("date_start"),
    date_end: url.searchParams.get("date_end"),
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
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(result.output),
  });

  if (!response.ok) {
    throw error(response.status, "Failed to fetch images");
  }

  return (await response.json()) as Promise<ImageSearchResult>;
};
