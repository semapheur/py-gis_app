<script lang="ts">
  import type { SvelteComponent, Snippet } from "svelte";
  import DropdownMenu from "$lib/components/DropdownMenu.svelte";

  interface Props {
    children: Snippet;
  }

  let { children }: Props = $props();
  let menu = $state<SvelteComponent | null>(null);
  let open = $state<boolean>(false);
</script>

<DropdownMenu bind:this={menu} bind:open>
  {#if menu}
    <button class="kebab-trigger" {...menu.triggerProps}>⋮</button>

    {#if open}
      <div class="kebab-menu" {...menu.menuProps}>
        {@render children?.()}
      </div>
    {/if}
  {/if}
</DropdownMenu>

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

    & :global(button[role="menuitem"]) {
      width: 100%;
      cursor: pointer;
    }
  }
</style>
