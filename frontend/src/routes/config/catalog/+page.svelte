<script lang="ts">
  import type { PageData } from "./$types";
  import { error } from "@sveltejs/kit";
  import { browser } from "$app/environment";
  import DataGrid from "$lib/components/DataGrid.svelte";

  async function verifyDir(path: string) {
    const response = await fetch("/api/verify-dir", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path }),
    });

    if (!response.ok) {
      throw error(response.status, `Failed to fetch area for id ${id}`);
    }

    const isValid = await response.json();

    return isValid;
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
      validate: verifyDir,
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
  $inspect(data);

  const addFill = {
    id: () => crypto.randomUUID(),
    createdByUserId: () => "",
    createdAtTimestamp: () => Date.now(),
    modifiedByUserId: () => null,
    modifiedAtTimestamp: () => null,
  };

  const editFill = {
    modifiedByUserId: () => "",
    modifiedAtTimestamp: () => Date.now(),
  };
</script>

{#if browser}
  <DataGrid {columns} data={data.catalogs} {addFill} {editFill} />
{/if}
