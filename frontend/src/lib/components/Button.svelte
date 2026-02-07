<script lang="ts">
  import type { Snippet } from "svelte";
  import type { HTMLButtonAttributes } from "svelte/elements";

  interface Props extends HTMLButtonAttributes {
    children: Snippet;
    background?: string;
  }

  let { children, background, ...rest }: Props = $props();
</script>

<button style:background-color={background ?? undefined} {...rest}>
  {@render children()}
</button>

<style>
  button {
    appearance: none;
    padding: var(--size-md);
    background-color: oklch(var(--color-secondary));
    border: none;
    border-radius: var(--size-sm);
    cursor: pointer;
    font-size: 1rem;
    font-weight: var(--font-bold);
  }
</style>
