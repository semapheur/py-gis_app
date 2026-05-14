import { error } from "@sveltejs/kit";
import { decode } from "@msgpack/msgpack";
import type { PageLoad } from "./$types";
import { type AttributeTableInfo } from "$lib/utils/types";

export const load: PageLoad = async ({ fetch }) => {
  const response = await fetch("/api/attribute-tables");

  if (!response.ok) {
    throw error(response.status, "Failed to load attribute tables");
  }

  const buffer = await response.arrayBuffer();
  const data: { tables: AttributeTableInfo[] } = decode(buffer);

  return data;
};
