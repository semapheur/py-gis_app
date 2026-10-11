<script lang="ts">
  import type { Snippet } from "svelte";
  import type { PageData } from "./$types";
  import LinkText from "#lib/components/LinkText.svelte";

  interface Props {
    data: PageData;
    children: Snippet;
  }

  let { data, children }: Props = $props();
</script>

<svelte:head>
  <title>Edit security attributes</title>
</svelte:head>

<div class="page-container">
  <nav class="table-list">
    <LinkText href="/config/edit-attributes/" label="Back" />
    <div data-sveltekit-replacestate>
      {#each data.tables as info (info.name)}
        <LinkText
          href={`/config/edit-attributes/security/${info.name}`}
          label={info.label}
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
