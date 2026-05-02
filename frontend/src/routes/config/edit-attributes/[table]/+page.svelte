<script lang="ts">
  import type { PageData } from "./$types";
  import { page } from "$app/state";
  import { browser } from "$app/environment";
  import DataGrid from "$lib/components/DataGrid.svelte";
  import { formatDatetime } from "$lib/utils/date";

  const columns = [
    { id: "id", header: "ID" },
    { id: "text", header: "Text", editor: "text", unique: true },
    { id: "description", header: "Description", editor: "textarea" },
    { id: "createdByUserId", header: "Created by" },
    {
      id: "createdAtTimestamp",
      header: "Created at",
      template: formatDatetime,
    },
    { id: "modifiedByUserId", header: "Modified by" },
    {
      id: "modifiedAtTimestamp",
      header: "Modified at",
      template: formatDatetime,
    },
  ];

  let { data }: { data: PageData } = $props();
  let table = $derived(page.params.table);

  let saveApi = $derived(table ? `/api/update-attributes/${table}` : undefined);

  const addFill = {
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
  <DataGrid {columns} data={data.data} {addFill} {editFill} {saveApi} />
{/if}
