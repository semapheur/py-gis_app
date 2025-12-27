<script lang="ts">
  import type { Snippet } from "svelte";

  interface Props {
    children: Snippet;
  }

  let { children }: Props = $props();

  let open = $state<boolean>(false);
  let container: HTMLDivElement | null = null;
  let trigger: HTMLButtonElement | null = null;
  let menu: HTMLDivElement | null = null;

  function toggle() {
    open = !open;
  }

  function close() {
    open = false;
  }

  function handleClickOutside(event: PointerEvent) {
    if (container && !container.contains(event.target as Node)) {
      close();
    }
  }

  function handleMenuClick(event: MouseEvent) {
    const item = (event.target as HTMLElement)?.closest('[role="menuitem"]');

    if (item) close();
  }

  $effect(() => {
    if (!open) {
      trigger?.focus();
      return;
    }

    queueMicrotask(() => menu?.focus());
    window.addEventListener("pointerdown", handleClickOutside);

    return () => {
      window.removeEventListener("pointerdown", handleClickOutside);
    };
  });

  function handleMenuKeydown(event: KeyboardEvent) {
    if (event.key === "Escape") {
      close();
      return;
    }

    if (event.key !== "ArrowDown" && event.key !== "ArrowUp") return;

    const items = Array.from(
      menu?.querySelectorAll<HTMLElement>('[role="menuitem"]') ?? [],
    );

    const index = items.indexOf(document.activeElement as HTMLElement);
    const next =
      event.key === "ArrowDown"
        ? (items[index + 1] ?? items[0])
        : (items[index - 1] ?? items[items.length - 1]);

    next?.focus();
    event.preventDefault();
  }

  function handleTriggerKeydown(event: KeyboardEvent) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      toggle();
    }
  }
</script>

<div class="kebab-container" bind:this={container}>
  <button
    bind:this={trigger}
    class="kebab-trigger"
    aria-haspopup="menu"
    aria-expanded={open}
    onclick={toggle}
    onkeydown={handleTriggerKeydown}
  >
    ⋮
  </button>

  {#if open}
    <div
      bind:this={menu}
      class="kebab-menu"
      role="menu"
      tabindex="-1"
      onclick={handleMenuClick}
      onkeydown={handleMenuKeydown}
    >
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

    & :global(button[role="menuitem"]) {
      width: 100%;
      cursor: pointer;
    }
  }
</style>
