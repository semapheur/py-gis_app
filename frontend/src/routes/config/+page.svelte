<script lang="ts">
  import { browser } from "$app/environment";
  import DataGrid from "$lib/components/DataGrid.svelte";
</script>

{#if browser}
  <DataGrid />
{/if}
