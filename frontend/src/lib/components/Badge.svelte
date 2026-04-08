<script lang="ts">
  import type { Snippet } from "svelte";

  type Variant = "default";

  interface Props {
    children: Snippet;
    variant?: Variant;
  }

  const { children, variant = "default" }: Props = $props();
</script>

<span class={variant}>
  {@render children()}
</span>

<style>
  span {
    font-size: var(--text-xs);
    border-radius: var(--size-sm);
    padding: 0 var(--size-sm);
  }

  .default {
    background-color: oklch(var(--color-secondary));
  }
</style>
