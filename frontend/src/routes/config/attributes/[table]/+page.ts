import { error } from "@sveltejs/kit";
import type { PageLoad } from "./$types";

export const load: PageLoad = async ({ params, fetch }) => {
  const table = params.table;

  if (!table) {
    throw error(400, "Missing table parameter");
  }

  const response = await fetch(`/api/attribute-data/${table}`);

  if (!response.ok) {
    throw error(response.status, "Failed to load attribute data");
  }

  const { data } = await response.json();

  return {
    data,
  };
};
