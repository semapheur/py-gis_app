import type { PageLoad } from "./$types";

export const load: PageLoad = async ({ fetch }) => {
  const response = await fetch("/api/attribute-tables");

  if (!response.ok) {
    throw new Error(`Failed to load tables: ${response.status}`);
  }

  const data: { tables: string[] } = await response.json();

  return {
    tables: data.tables,
  };
};
