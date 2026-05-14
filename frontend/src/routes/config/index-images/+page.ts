import { error } from "@sveltejs/kit";
import { decode } from "@msgpack/msgpack";
import type { PageLoad } from "./$types";

export const load: PageLoad = async ({ fetch }) => {
  const response = await fetch("/api/get-catalogs-index");

  if (!response.ok) {
    throw error(response.status, "Failed to load catalogs");
  }

  const buffer = await response.arrayBuffer();
  const { catalogs } = decode(buffer);

  return {
    catalogs,
  };
};
