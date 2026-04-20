import { error } from "@sveltejs/kit";
import type { PageLoad } from "./$types";

export const load: PageLoad = async ({ params, fetch }) => {
  const response = await fetch("/api/get-catalogs");

  if (!response.ok) {
    throw error(response.status, "Failed to load catalogs");
  }

  const { data } = await response.json();

  return {
    data,
  };
};
