<script lang="ts">
  import type { PageData } from "./$types";
  import { browser } from "$app/environment";
  import DataGrid from "$lib/components/DataGrid.svelte";
  import type { DataGridColumn } from "$lib/utils/types";

  const columns = [
    { id: "identifier", header: "Identifier", editor: "text", required: true },
    {
      id: "display_name",
      header: "Display name",
      editor: "text",
      required: true,
      unique: true,
    },
    {
      id: "description",
      header: "Description",
      editor: "textarea",
      required: true,
    },
    {
      id: "description_short",
      header: "Description (short)",
      editor: "text",
      required: true,
    },
    { id: "natoName", header: "NATO name", editor: "text", required: false },
    {
      id: "native_name",
      header: "Native name",
      editor: "text",
      required: false,
    },
    {
      id: "alternative_names",
      header: "Alternative names",
      editor: "text",
      required: false,
    },
    { id: "source", header: "Source", editor: "text", required: false },
    {
      id: "source_data",
      header: "Source data",
      editor: "textarea",
      required: false,
    },
  ] satisfies DataGridColumn[];
  let { data }: { data: PageData } = $props();
</script>

{#if browser}
  <DataGrid
    {columns}
    data={data.equipment}
    insertApi="/api/insert-equipment"
    updateApi="/api/update-equipment"
    deleteApi=""
  />
{/if}
