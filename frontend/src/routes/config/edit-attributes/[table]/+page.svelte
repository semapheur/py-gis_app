<script lang="ts">
  import type { PageData } from "./$types";
  import { page } from "$app/state";
  import { browser } from "$app/environment";
  import DataGrid from "$lib/components/DataGrid.svelte";
  import { formatDatetime } from "$lib/utils/date";

  const columns = [
    { id: "schema", header: "Schema", editor: "text" },
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

  let insertApi = $derived(`/api/insert-attribute/${table}`);
  let updateApi = $derived(`/api/update-attribute/${table}`);
  let deleteApi = $derived(`/api/delete-attribute/${table}`);
</script>

{#if browser}
  <DataGrid {columns} data={data.data} {insertApi} {updateApi} {deleteApi} />
{/if}
