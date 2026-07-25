<script lang="ts">
  import type { HTMLAnchorAttributes } from "svelte/elements";
  import { page } from "$app/state";

  interface Props extends HTMLAnchorAttributes {
    label: string;
  }

  const { children, label, href, ...rest }: Props = $props();

  const isActive = $derived(href != null && page.url.pathname === href);
</script>

<a
  {href}
  {...rest}
  class={{ active: isActive }}
  aria-current={isActive ? "page" : undefined}
>
  <span class="label" data-text={label}>
    {label}
  </span>
</a>

<style>
  a {
    display: grid;
    color: inherit;
    text-decoration: none;

    &:hover {
      color: oklch(var(--color-secondary));
    }

    &.active .label {
      color: oklch(var(--color-secondary));
      font-weight: var(--font-bold);
    }
  }

  .label {
    grid-area: 1 / 1;
    font-weight: 400;

    &::after {
      content: attr(data-text);
      display: block;
      height: 0;
      overflow: hidden;
      font-weight: var(--font-bold);
      visibility: hidden;
    }
  }
</style>
