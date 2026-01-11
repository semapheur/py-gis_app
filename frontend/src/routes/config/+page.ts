import type { PageLoad } from "./$types";

export const load: PageLoad = async ({ fetch }) => {
  const response = await fetch("/api/attribute-schemas");

  if (!response.ok) {
    throw new Error(`Failed to load attribute schemas: ${response.status}`);
  }

  const data: { schemas: string[] } = await response.json();

  return {
    schemas: data.schemas,
  };
};
