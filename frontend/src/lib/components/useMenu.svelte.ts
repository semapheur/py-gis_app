export function useMenu() {
  let open = $state(false);

  let container: HTMLElement | null = null;
  let menu: HTMLElement | null = null;
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

  $effect(() => {
    if (!open) return;

    queueMicrotask(() => menu?.focus());
    window.addEventListener("pointerdown", handleClickOutside);

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
    containerProps: {
      "@attach": (el: HTMLElement) => (container = el),
    },
    menuProps: {
      "@attach": (el: HTMLElement) => (menu = el),
      role: "menu",
      tabindex: -1,
      onkeydown: handleMenuKeydown,
      onclick: handleMenuClick,
    },
  };
}
