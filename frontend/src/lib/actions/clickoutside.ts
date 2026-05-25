export function clickoutside(node: HTMLElement, callback: () => void) {
  function handle(e: PointerEvent) {
    if (!node.contains(e.target as Node)) {
      callback();
    }
  }

  document.addEventListener("pointerdown", handle);
  return {
    destroy() {
      document.removeEventListener("pointerdown", handle);
    },
  };
}
