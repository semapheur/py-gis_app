import { error } from "@sveltejs/kit";
import type { PageLoad } from "./$types";

export const load: PageLoad = async ({ fetch }) => {
  const response = await fetch("/api/attribute-tables");

  if (!response.ok) {
    throw error(response.status, "Failed to load attribute tables");
  }

  const data: { tables: string[] } = await response.json();

  return data;
};
