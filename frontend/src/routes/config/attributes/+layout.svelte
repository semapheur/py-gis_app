<script lang="ts">
  import type { Snippet } from "svelte";
  import type { PageData } from "./$types";

  interface Props {
    data: PageData;
    children: Snippet;
  }

  let { data, children }: Props = $props();
</script>

<div class="page-container">
  <nav class="table-list">
    {#each data.tables as info}
      <a href={`/config/attributes/${info.table_name}`}>{info.label}</a>
    {/each}
  </nav>
  {@render children()}
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
