import { error } from "@sveltejs/kit";
import type { PageLoad } from "./$types";

export const load: PageLoad = async ({ fetch }) => {
  const response = await fetch("/api/get-equipment");

  if (!response.ok) {
    throw error(response.status, "Failed to load equipment");
  }

  const { equipment } = await response.json();

  return {
    equipment,
  };
};
