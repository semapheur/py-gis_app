import { tick } from "svelte";

export function useMenu() {
  let open = $state(false);
  let container = $state<HTMLElement | null>(null);
  let menu = $state<HTMLElement | null>(null);

  let restoreFocusTo: HTMLElement | null = null;

  function openMenu({ restoreFocus }: { restoreFocus?: HTMLElement } = {}) {
    restoreFocusTo = restoreFocus ?? null;
    open = true;
  }

  function closeMenu() {
    open = false;
    restoreFocusTo?.focus();
    restoreFocusTo = null;
  }

  function handleClickOutside(event: PointerEvent) {
    if (container && !container.contains(event.target as Node)) {
      closeMenu();
    }
  }

  function handleMenuKeydown(event: KeyboardEvent) {
    switch (event.key) {
      case "Escape": {
        closeMenu();
        break;
      }

      case "ArrowDown":
      case "ArrowUp": {
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
        break;
      }

      default: {
        break;
      }
    }
  }

  function handleMenuClick(event: MouseEvent) {
    const item = (event.target as HTMLElement)?.closest('[role="menuitem"]');
    if (item) closeMenu();
  }

  function setContainer(el: HTMLElement) {
    container = el;
  }

  function setMenu(el: HTMLElement) {
    menu = el;
  }

  $effect(() => {
    if (!open) return;

    tick().then(() => {
      menu?.focus();
      window.addEventListener("pointerdown", handleClickOutside);
    });

    return () => {
      window.removeEventListener("pointerdown", handleClickOutside);
    };
  });

  return {
    get open() {
      return open;
    },
    openMenu,
    closeMenu,
    setContainer,
    setMenu,
    menuProps: {
      role: "menu",
      tabindex: -1,
      onkeydown: handleMenuKeydown,
      onclick: handleMenuClick,
    },
  };
}
