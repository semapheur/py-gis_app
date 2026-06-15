import { error } from "@sveltejs/kit";
import { decode } from "@msgpack/msgpack";
import type { PageLoad } from "./$types";
import type { AttributeData, SchemaDataOption } from "$lib/utils/types";

export const load: PageLoad = async ({ params, fetch }) => {
  const table = params.table;

  if (!table) {
    throw error(400, "Missing table parameter");
  }

  const [schemaResponse, attributeResponse] = await Promise.all([
    table !== "schema" ? fetch("/api/schema-data-options") : null,
    fetch(`/api/attribute-data/${table}`),
  ]);

  if (schemaResponse && !schemaResponse.ok) {
    throw error(schemaResponse.status, "Failed to load schema options");
  }

  if (attributeResponse && !attributeResponse.ok) {
    throw error(attributeResponse.status, "Failed to load attribute data");
  }

  const [schemaBuffer, attributeBuffer] = await Promise.all([
    schemaResponse ? schemaResponse.arrayBuffer() : null,
    attributeResponse.arrayBuffer(),
  ]);

  const schemaOptions = schemaBuffer
    ? (decode(schemaBuffer) as { options: SchemaDataOption[] }).options
    : null;

  const { data } = decode(attributeBuffer) as { data: AttributeData[] };

  return {
    data,
    schemaOptions,
  };
};
