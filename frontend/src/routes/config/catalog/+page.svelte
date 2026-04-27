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

    if (response.ok) {
      return true;
    }

    const { detail } = await response.json();
    throw new Error(detail);
  }

  const formatDatetime = (v: number) =>
    v ? new Date(v).toISOString() : undefined;

  const columns = [
    { id: "id", header: "ID", flexgrow: 1 },
    { id: "name", header: "Name", editor: "text", flexgrow: 1 },
    {
      id: "path",
      header: "Folder path",
      editor: "text",
      validate: validateCatalogPath,
      flexgrow: 1,
    },
    {
      id: "last_indexed",
      header: "Last indexed",
      template: formatDatetime,
      flexgrow: 1,
    },
  ];

  let { data }: { data: PageData } = $props();
</script>

{#if browser}
  <DataGrid {columns} data={data.catalogs} />
{/if}
