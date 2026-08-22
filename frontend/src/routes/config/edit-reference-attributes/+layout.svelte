<script lang="ts">
  import type { Snippet } from "svelte";
  import LinkText from "$lib/components/LinkText.svelte";

  interface Props {
    children: Snippet;
  }

  const tables = [
    {
      name: "originator",
      label: "Originator",
    },
    {
      name: "source_type",
      label: "Source type",
    },
  ];
  let { children }: Props = $props();
</script>

<div class="page-container">
  <nav class="table-list">
    {#each tables as table}
      <LinkText
        href={`/config/edit-reference-attributes/${table.name}`}
        label={table.label}
      />
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
