<script lang="ts">
  import { type Snippet } from "svelte";
  import type { HTMLAnchorAttributes } from "svelte/elements";

  interface Props extends HTMLAnchorAttributes {
    children: Snippet;
  }

  const { children, ...rest }: Props = $props();
</script>

<a {...rest}>
  {@render children()}
</a>

<style>
  a {
    color: inherit;
    text-decoration: none;

    &:hover {
      color: oklch(var(--color-secondary));
    }
  }
</style>
