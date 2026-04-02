<script lang="ts">
  import { type Snippet } from "svelte";
  import type { HTMLAnchorAttributes } from "svelte/elements";

  type TooltipPlacement = "top" | "bottom" | "left" | "right";

  interface Props extends HTMLAnchorAttributes {
    children: Snippet;
    tooltip?: string;
    tooltipPlacement?: TooltipPlacement;
  }

  const { children, tooltip, tooltipPlacement, ...rest }: Props = $props();
</script>

<a
  {...rest}
  data-tooltip={tooltip}
  data-tooltip-placement={tooltip ? tooltipPlacement : undefined}
>
  {@render children()}
</a>

<style>
  a {
    color: inherit;
    text-decoration: none;
  }

  a[data-tooltip] {
    position: relative;
  }

  a[data-tooltip]::after {
    content: attr(data-tooltip);
    display: none;
    position: absolute;
    z-index: 1;
    padding: 0 var(--size-sm);
    background-color: oklch(var(--color-primary));
    border: 1px solid oklch(var(--color-accent));
    border-radius: var(--size-sm);
    font-size: var(--text-xs);
    white-space: nowrap;
  }

  a[data-tooltip]:hover::after {
    display: block;
  }

  a[data-tooltip-placement="top"]::after {
    bottom: calc(100% + var(--size-lg));
    left: 50%;
    transform: translateX(-50%);
  }

  /* Bottom */
  a[data-tooltip-placement="bottom"]::after {
    top: calc(100% + var(--size-lg));
    left: 50%;
    transform: translateX(-50%);
  }

  /* Left */
  a[data-tooltip-placement="left"]::after {
    right: calc(100% + var(--size-lg));
    top: 50%;
    transform: translateY(-50%);
  }

  /* Right */
  a[data-tooltip-placement="right"]::after {
    left: calc(100% + var(--size-lg));
    top: 50%;
    transform: translateY(-50%);
  }
</style>
