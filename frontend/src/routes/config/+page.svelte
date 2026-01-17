<script lang="ts">
  import type { PageData } from "./$types";
  import { browser } from "$app/environment";
  import DataGrid from "$lib/components/DataGrid.svelte";

  const metaColumns = [
    { id: "id", header: "ID" },
    { id: "createdByUserId", header: "Created by" },
    { id: "createdAtTimestamp", header: "Created at" },
    { id: "modifiedByUserId", header: "Modified by" },
    { id: "modifiedAtTimestamp", header: "Modified at" },
  ];

  let { data }: { data: PageData } = $props();
  let selectedTable = $state<string>("");
  let saveApi = $derived(
    selectedTable ? `/api/update-attributes/${selectedTable}` : undefined,
  );
  let columns = $derived(
    selectedTable
      ? [...metaColumns, ...data.schemas[selectedTable].columns]
      : [],
  );
  let inputIds = $derived(
    selectedTable
      ? new Set(data.schemas[selectedTable].columns.map((c) => c.id))
      : undefined,
  );

  const autoFill = {
    id: () => crypto.randomUUID(),
    createdByUserId: () => "",
    createdAtTimestamp: () => Date.now(),
    modifiedByUserId: () => null,
    modifiedAtTimestamp: () => null,
  };
</script>

<div class="page-container">
  <nav class="table-list">
    {#each Object.entries(data.schemas) as [tableName, schema]}
      <button onclick={() => (selectedTable = tableName)}>{schema.label}</button
      >
    {/each}
  </nav>
  {#if browser}
    <DataGrid {columns} data={[]} {autoFill} {inputIds} {saveApi} />
  {/if}
</div>

<style>
  .page-container {
    display: grid;
    grid-template-columns: auto 1fr;
  }

  .table-list {
    display: flex;
    flex-direction: column;
  }
</style>
