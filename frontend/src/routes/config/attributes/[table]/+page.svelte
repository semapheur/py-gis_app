<script lang="ts">
  import type { PageData } from "./$types";
  import { page } from "$app/state";
  import { browser } from "$app/environment";
  import DataGrid from "$lib/components/DataGrid.svelte";

  const formatDatetime = (v: number) =>
    v ? new Date(v).toISOString() : undefined;

  const metaColumns = [
    { id: "id", header: "ID" },
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
  let columns = $derived([...metaColumns, ...data.columns]);

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
  <DataGrid {columns} data={data.data} {addFill} {editFill} {saveApi} />
{/if}
