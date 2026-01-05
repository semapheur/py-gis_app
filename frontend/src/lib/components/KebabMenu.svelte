<script lang="ts">
  import type { Snippet } from "svelte";
  import { useMenu } from "$lib/hooks/useMenu.svelte";

  interface Props {
    children: Snippet;
  }

  let { children }: Props = $props();
  const menu = useMenu();
  let trigger: HTMLElement | null = null;

  function toggle() {
    menu.open ? menu.closeMenu() : menu.openMenu({ restoreFocus: trigger! });
  }
</script>

<div {...menu.containerProps}>
  <button
    {@attach (el) => {
      trigger = el;
    }}
    class="kebab-trigger"
    aria-haspopup="menu"
    aria-expanded={menu.open}
    onclick={toggle}
  >
    ⋮
  </button>

  {#if menu.open}
    <div class="kebab-menu" {...menu.menuProps}>
      {@render children?.()}
    </div>
  {/if}
</div>

<style>
  .kebab-trigger {
    all: unset;
    cursor: pointer;
    font-size: var(--text-lg);
    font-weight: var(--font-bold);
  }

  .kebab-menu {
    position: absolute;
    display: flex;
    flex-direction: column;
    background: rgb(var(--color-accent));
    border: 1px solid rgba(var(--color-text));
    z-index: 1;

    & :global(button[role="menuitem"]) {
      all: unset;
      width: 100%;
      cursor: pointer;
      text-align: left;
      padding: 0 var(--size-md);

      &:not(:last-child) {
        border-bottom: 1px solid rgba(var(--color-text) / 0.5);
      }

      &:hover,
      &:focus-visible {
        background: rgba(var(--color-primary) / 0.5);
      }
    }
  }
</style>
