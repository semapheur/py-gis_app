import { error } from "@sveltejs/kit";
import * as v from "valibot";
import type { PageLoad } from "./$types";
import type { ImageMetadata } from "#lib/utils/types.js";
import { searchSchema } from "#lib/schemas/image_search.js";
import { loadMsgpack } from "#lib/utils/msgpack.js";

export const prerender = false;

interface ImageSearchResult {
  wkt: string | null;
  images: ImageMetadata[];
}

export const load: PageLoad = async ({ fetch, url }) => {
  const { area, ...params } = Object.fromEntries(
    [...url.searchParams].filter(([, value]) => value !== ""),
  );

  const result = v.safeParse(searchSchema, { ...params, area_id: area });

  if (!result.success) {
    const { root = [], nested = {} } = v.flatten(result.issues);
    const messages = [
      ...root,
      ...Object.entries(nested).map(
        ([field, errors]) => `${field}: ${errors?.join(", ")}`,
      ),
    ];

    throw error(400, `Invalid search parameters: ${messages.join("; ")}`);
  }

  return loadMsgpack<ImageSearchResult>(fetch, "/api/search-images", {
    method: "POST",
    body: result.output,
  });
};
