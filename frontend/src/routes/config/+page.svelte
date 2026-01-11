<script lang="ts">
  import { browser } from "$app/environment";
  import DataGrid from "$lib/components/DataGrid.svelte";

  let { data }: { data: PageData } = $props();
  let selectedTable = $state<string>("");

  console.log(data.tables);
</script>

<div class="page-container">
  <nav class="table-list">
    {#each data.tables as table}
      <button>{table}</button>
    {/each}
  </nav>
  {#if browser}
    <DataGrid />
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
