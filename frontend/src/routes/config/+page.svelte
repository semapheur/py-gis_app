<script lang="ts">
  import { browser } from "$app/environment";
  import DataGrid from "$lib/components/DataGrid.svelte";

  let { data }: { data: PageData } = $props();
</script>

{#if browser}
  <DataGrid />
{/if}
