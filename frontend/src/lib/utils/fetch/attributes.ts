import { error } from "@sveltejs/kit";
import { decode } from "@msgpack/msgpack";
import { type AttributeData, type TableNameLabel } from "#lib/utils/types.js";

type AttributeType = "annotation" | "reference" | "security";

export async function loadAttributeTables(
  fetch: typeof globalThis.fetch,
  type: AttributeType,
): Promise<{ tables: TableNameLabel[] }> {
  const response = await fetch(
    `/api/attribute-tables?type=${encodeURIComponent(type)}`,
  );

  if (!response.ok) {
    throw error(response.status, "Failed to load attribute tables");
  }

  return decode(await response.arrayBuffer()) as { tables: TableNameLabel[] };
}

export async function loadAttributeData(
  fetch: typeof globalThis.fetch,
  table: string,
): Promise<{ data: AttributeData[] }> {
  const response = await fetch(
    `/api/attribute-data?table=${encodeURIComponent(table)}`,
  );

  if (!response.ok) {
    throw error(response.status, "Failed to load attribute data");
  }

  const { data } = decode(await response.arrayBuffer()) as {
    data: AttributeData[];
  };

  return { data };
}
