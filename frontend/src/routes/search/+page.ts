import type { PageLoad } from "./$types";
import type { ImageMetadata } from "$lib/utils/types";

export const load: PageLoad = async ({ fetch, url }) => {
  const encodedWkt = url.searchParams.get("wkt");

  let wkt: string;
  try {
    wkt = decodeURIComponent(encodedWkt);
  } catch {
    throw new Error("Invalid WKT encoding");
  }

  const response = await fetch("/api/query-images", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ wkt }),
  });

  if (!response.ok) {
    throw new Error("Failed to fetch images intersecting extent");
  }

  const images: ImageMetadata = await response.json();

  return {
    images,
  };
};
