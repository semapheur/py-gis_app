import type { PageLoad } from "./$types";
import { error } from "@sveltejs/kit";

export const load: PageLoad = async ({ params, fetch }) => {
  const table = params.table;

  if (!table) {
    throw error(400, "Missing table parameter");
  }

  const request = {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ table }),
  };

  const [schemaResponse, dataResponse] = await Promise.all([
    fetch("/api/attribute-schema", request),
    fetch("/api/attribute-data", request),
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
