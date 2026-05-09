import { error } from "@sveltejs/kit";
import type { PageLoad } from "./$types";
import { type AttributeTableInfo } from "$lib/utils/types";

export const load: PageLoad = async ({ fetch }) => {
  const response = await fetch("/api/attribute-tables");

  if (!response.ok) {
    throw error(response.status, "Failed to load attribute tables");
  }

  const data: { tables: AttributeTableInfo[] } = await response.json();

  return data;
};
