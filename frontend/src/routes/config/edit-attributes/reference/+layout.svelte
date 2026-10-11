<script lang="ts">
  import type { Snippet } from "svelte";
  import LinkText from "#lib/components/LinkText.svelte";

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

<svelte:head>
  <title>Edit reference attributes</title>
</svelte:head>

<div class="page-container">
  <nav class="table-list">
    <LinkText href="/config/edit-attributes/" label="Back" />
    <div data-sveltekit-replacestate>
      {#each tables as table}
        <LinkText
          href={`/config/edit-attributes/reference/${table.name}`}
          label={table.label}
        />
      {/each}
    </div>
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
