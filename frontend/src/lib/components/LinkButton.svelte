<script lang="ts">
  import type { Snippet } from "svelte";
  import type { HTMLAnchorAttributes } from "svelte/elements";

  interface Props extends HTMLAnchorAttributes {
    children: Snippet;
    background?: string;
  }

  let { children, background, ...rest }: Props = $props();
</script>

<a style:background-color={background ?? undefined} {...rest}>
  {@render children()}
</a>

<style>
  a {
    color: inherit;
    text-decoration: none;
    font: inherit;
    padding: var(--size-md);
    background-color: oklch(var(--color-secondary));
    border: none;
    border-radius: var(--size-sm);
    cursor: pointer;
    font-size: var(--text-sm);
    font-weight: var(--font-bold);
  }
</style>
