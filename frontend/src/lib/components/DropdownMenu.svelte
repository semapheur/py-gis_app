<script lang="ts">
  import type { Snippet } from "svelte";
  import { useMenu } from "$lib/components/useMenu.svelte";
  import type { HTMLButtonAttributes } from "svelte/elements";

  interface Props {
    children: Snippet;
    open?: boolean;
  }

  let { children, open = $bindable(false) }: Props = $props();

  const menu = useMenu();
  let trigger: HTMLElement | null = null;

  $effect(() => {
    open = menu.open;
  });

  function toggle() {
    menu.open ? menu.closeMenu() : menu.openMenu({ restoreFocus: trigger! });
  }

  function handleTriggerKeydown(event: KeyboardEvent) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      toggle();
    }

    if (event.shiftKey && event.key === "F10") {
      menu.openMenu();
    }
  }

  export const triggerProps: HTMLButtonAttributes = {
    "@attach": (el: HTMLElement) => (trigger = el),
    role: "button",
    "aria-haspopup": "menu",
    "aria-expanded": menu.open,
    onclick: toggle,
    onkeydown: handleTriggerKeydown,
  };

  export const menuProps = menu.menuProps;
</script>

<div {...menu.containerProps}>
  {@render children?.()}
</div>
