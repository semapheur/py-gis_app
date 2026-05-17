<script lang="ts">
  import type { PageData } from "./$types";
  import { browser } from "$app/environment";
  import DataGrid from "$lib/components/DataGrid.svelte";
  import { formatDatetime } from "$lib/utils/date";

  const columns = [
    { id: "id", header: "ID" },
    { id: "identifier", header: "Identifier", editor: "text" },
    { id: "displayName", header: "Display name", editor: "text", unique: true },
    { id: "description", header: "Description", editor: "textarea" },
    { id: "descriptionShort", header: "Description (short)", editor: "text" },
    { id: "natoName", header: "NATO name", editor: "text" },
    { id: "nativeName", header: "Native name", editor: "text" },
    { id: "alternativeNames", header: "Alternative names", editor: "text" },
    { id: "source", header: "Source", editor: "text" },
    { id: "sourceData", header: "Source data", editor: "textarea" },
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
  <DataGrid
    {columns}
    data={data.equipment}
    {addFill}
    {editFill}
    saveApi="/api/update-equipment"
  />
{/if}
