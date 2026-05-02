import { error } from "@sveltejs/kit";
import type { PageLoad } from "./$types";

export const load: PageLoad = async ({ fetch }) => {
  const response = await fetch("/api/get-catalogs-edit");

  if (!response.ok) {
    throw error(response.status, "Failed to load catalog data");
  }

  const { catalogs } = await response.json();

  return {
    catalogs,
  };
};
