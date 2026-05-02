import { error } from "@sveltejs/kit";
import type { PageLoad } from "./$types";

export const load: PageLoad = async ({ fetch }) => {
  const response = await fetch("/api/get-catalogs-index");

  if (!response.ok) {
    throw error(response.status, "Failed to load catalogs");
  }

  const { catalogs } = await response.json();

  return {
    catalogs,
  };
};
