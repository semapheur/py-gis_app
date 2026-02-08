<script lang="ts">
  import type { Snippet } from "svelte";

  interface Props {
    children: Snippet;
  }

  let { children }: Props = $props();
</script>

<div class="input-group">
  {@render children()}
</div>

<style>
  .input-group {
    display: flex;
    align-items: stretch;

    & > :global(*) {
      border-radius: 0;
    }

    & > :global(*:first-child) {
      border-top-left-radius: var(--size-md);
      border-bottom-left-radius: var(--size-md);
    }

    & > :global(*:last-child) {
      border-top-right-radius: var(--size-md);
      border-bottom-right-radius: var(--size-md);
    }

    & > :global(* + *) {
      margin-left: -1px;
    }
  }
</style>
