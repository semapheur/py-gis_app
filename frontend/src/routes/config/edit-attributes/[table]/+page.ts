import { error } from "@sveltejs/kit";
import { decode } from "@msgpack/msgpack";
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

  const buffer = await response.arrayBuffer();
  const { data } = decode(buffer);

  return {
    data,
  };
};
