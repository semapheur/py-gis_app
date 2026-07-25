<script lang="ts">
  import type { Snippet } from "svelte";
  import type { PageData } from "./$types";
  import LinkText from "$lib/components/LinkText.svelte";

  interface Props {
    data: PageData;
    children: Snippet;
  }

  let { data, children }: Props = $props();
</script>

<div class="page-container">
  <nav class="table-list">
    <LinkText
      href="/config/edit-security/classification"
      label="Classification"
    />
    <LinkText
      href="/config/edit-security/releasability"
      label="Releasability"
    />
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
