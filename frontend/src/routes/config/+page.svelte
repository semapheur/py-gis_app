<script lang="ts">
  import { browser } from "$app/environment";
  import DataGrid from "$lib/components/DataGrid.svelte";

  let { data }: { data: PageData } = $props();
  let selectedTable = $state<string>("");
  let columns = $derived.by(() => {
    if (!selectedTable) return [];

    return data.schemas[selectedTable].columns;
  });
</script>

<div class="page-container">
  <nav class="table-list">
    {#each Object.entries(data.schemas) as [tableName, schema]}
      <button onclick={() => (selectedTable = tableName)}>{schema.label}</button
      >
    {/each}
  </nav>
  {#if browser}
    <DataGrid {columns} data={[]} />
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
