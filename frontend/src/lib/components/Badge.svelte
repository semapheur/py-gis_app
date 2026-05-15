<script lang="ts">
  import type { Snippet } from "svelte";

  type Variant = "default";

  interface Props {
    children: Snippet;
    tooltip?: string;
    variant?: Variant;
  }

  const { children, tooltip, variant = "default" }: Props = $props();
</script>

<span class={variant} title={tooltip}>
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
