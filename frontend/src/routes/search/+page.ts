import { error } from "@sveltejs/kit";
import type { PageLoad } from "./$types";
import type { ImageMetadata } from "$lib/utils/types";
import type { AreaInfo } from "$lib/contexts/area_editor.svelte";
import { polygonToWkt } from "$lib/utils/geo/wkt";

interface ImageSearchResult {
  wkt: string | null;
  images: ImageMetadata;
}

export const load: PageLoad = async ({ fetch, url }) => {
  const wkt = url.searchParams.get("wkt");
  const areaId = url.searchParams.get("area");

  const response = await fetch("/api/search-images", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ wkt, area_id: areaId }),
  });

  if (!response.ok) {
    throw error(response.status, "Failed to fetch images");
  }

  return (await response.json()) as Promise<ImageSearchResult>;
};
