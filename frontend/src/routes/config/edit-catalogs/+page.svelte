<script lang="ts">
  import type { PageData } from "./$types";
  import { browser } from "$app/environment";
  import DataGrid from "$lib/components/DataGrid.svelte";

  async function validateCatalogPath(path: string) {
    const response = await fetch("/api/validate-catalog-dir", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path }),
    });

    if (response.ok) return true;

    let message = `Validation failed (${response.status})`;
    const body = await response.json().catch(() => null);
    if (body.detail) message = body.detail;
    throw new Error(message);
  }

  const columns = [
    { id: "id", header: "ID", flexgrow: 1 },
    { id: "name", header: "Name", editor: "text", flexgrow: 1, unique: true },
    {
      id: "path",
      header: "Folder path",
      editor: "text",
      flexgrow: 1,
      validate: validateCatalogPath,
      unique: true,
    },
  ];

  let { data }: { data: PageData } = $props();
</script>

{#if browser}
  <DataGrid {columns} data={data.catalogs} saveApi="/api/update-catalogs" />
{/if}
