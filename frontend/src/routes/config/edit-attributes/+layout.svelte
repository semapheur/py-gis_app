<script lang="ts">
  import type { Snippet } from "svelte";
  import type { PageData } from "./$types";
  import Link from "$lib/components/Link.svelte";

  interface Props {
    data: PageData;
    children: Snippet;
  }

  let { data, children }: Props = $props();
</script>

<div class="page-container">
  <nav class="table-list">
    {#each data.tables as info}
      <Link href={`/config/attributes/${info.name}`}>{info.label}</Link>
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
    gap: var(--size-sm);
    padding: var(--size-lg);
  }
</style>
