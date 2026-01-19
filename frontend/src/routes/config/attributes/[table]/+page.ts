import { error } from "@sveltejs/kit";
import type { PageLoad } from "./$types";

export const load: PageLoad = async ({ params, fetch }) => {
  const table = params.table;

  if (!table) {
    throw error(400, "Missing table parameter");
  }

  const [schemaResponse, dataResponse] = await Promise.all([
    fetch(`/api/attribute-schema/${table}`),
    fetch(`/api/attribute-data/${table}`),
  ]);

  if (!schemaResponse.ok) {
    throw error(schemaResponse.status, "Failed to load attribute schema");
  }

  if (!dataResponse.ok) {
    throw error(dataResponse.status, "Failed to load attribute data");
  }

  const { columns } = await schemaResponse.json();
  const { data } = await dataResponse.json();

  return {
    columns,
    data,
  };
};
