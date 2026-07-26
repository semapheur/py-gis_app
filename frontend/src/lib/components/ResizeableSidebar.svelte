<script lang="ts">
  import type { Snippet } from "svelte";

  interface Props {
    side: "left" | "right";
    widthPercent: number;
    minWidthPercent: number;
    maxWidthPercent: number;
    children: Snippet;
  }

  let {
    side,
    widthPercent,
    minWidthPercent,
    maxWidthPercent,
    children,
  }: Props = $props();

  let isResizing = $state<boolean>(false);
  let sidebarEl = $state<HTMLDivElement | null>(null);
  let parentWidth = $state<number>(0);

  const widthPx = $derived((widthPercent / 100) * parentWidth);

  $effect(() => {
    const parent = sidebarEl?.offsetParent as HTMLElement | null;
    if (!parent) return;

    const observer = new ResizeObserver((entries) => {
      parentWidth = entries[0].contentRect.width;
    });
    observer.observe(parent);

    return () => observer.disconnect();
  });

  $effect(() => {
    if (widthPercent > maxWidthPercent) widthPercent = maxWidthPercent;
    if (widthPercent < minWidthPercent) widthPercent = minWidthPercent;
  });

  function startResize(e: PointerEvent) {
    isResizing = true;
    e.preventDefault();

    const startX = e.clientX;
    const startPercent = widthPercent;
    const sign = side === "right" ? -1 : 1;

    function onPointerMove(moveEvent: PointerEvent) {
      if (!parentWidth) return;

      const deltaPx = (moveEvent.clientX - startX) * sign;
      const deltaPercent = (deltaPx / parentWidth) * 100;
      const proposed = startPercent + deltaPercent;

      widthPercent = Math.min(
        maxWidthPercent,
        Math.max(minWidthPercent, proposed),
      );
    }

    function onPointerUp() {
      isResizing = false;
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("pointerup", onPointerUp);
    }

    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerup", onPointerUp);
  }
</script>

<div
  bind:this={sidebarEl}
  class={["sidebar", { left: side === "left", right: side === "right" }]}
  style="width: {widthPercent}%"
>
  <div
    class={["resize-handle", { resizing: isResizing }]}
    onpointerdown={startResize}
    role="separator"
    aria-orientation="vertical"
    aria-valuenow={widthPercent}
    aria-valuemin={minWidthPercent}
    aria-valuemax={maxWidthPercent}
  ></div>
  <div class="sidebar-content">
    {@render children()}
  </div>
</div>

<style>
  .sidebar {
    display: flex;
    flex-direction: column;
    position: absolute;
    top: 0;
    height: 100%;
    background-color: oklch(var(--color-primary));
    z-index: 2;
  }

  .sidebar.right {
    right: 0;
  }

  .sidebar.left {
    left: 0;
  }

  .sidebar-content {
    height: 100%;
    overflow: hidden;
  }

  .resize-handle {
    position: absolute;
    top: 0;
    width: 0;
    height: 100%;
    cursor: col-resize;
    z-index: 3;
    background: transparent;
  }

  .sidebar.right .resize-handle {
    left: 0;
  }

  .sidebar.left .resize-handle {
    right: 0;
  }

  .resize-handle::after {
    content: "";
    position: absolute;
    top: 0;
    width: 2px;
    height: 100%;
    background: oklch(var(--color-secondary-accent));
    opacity: 0;
    transition: opacity 0.15s;
  }

  .resize-handle:hover::after,
  .resize-handle.resizing::after {
    opacity: 1;
  }
</style>
