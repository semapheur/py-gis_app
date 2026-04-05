<script lang="ts">
  import { type Snippet } from "svelte";
  import { type HTMLButtonAttributes } from "svelte/elements";

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
    display: inline-flex;
    align-items: center;
    gap: var(--size-sm);
    appearance: none;
    padding: var(--size-md);
    color: inherit;
    background-color: oklch(var(--color-secondary));
    border: none;
    border-radius: var(--size-sm);
    cursor: pointer;
    font-size: var(--text-sm);
    font-weight: var(--font-bold);
    line-height: var(--button-line-height);

    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  }
</style>
