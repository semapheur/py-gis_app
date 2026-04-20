<script lang="ts">
  import type { PageData } from "./$types";
  import { browser } from "$app/environment";
  import DataGrid from "$lib/components/DataGrid.svelte";

  const formatDatetime = (v: number) =>
    v ? new Date(v).toISOString() : undefined;

  const columns = [
    { id: "id", header: "ID" },
    { id: "name", header: "Name", editor: "text" },
    { id: "path", header: "Folder path", editor: "directory" },
    {
      id: "last_indexed",
      header: "Last indexed",
      template: formatDatetime,
    },
  ];

  let { data }: { data: PageData } = $props();

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
  <DataGrid {columns} data={data.data} {addFill} {editFill} />
{/if}
