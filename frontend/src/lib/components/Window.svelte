<script lang="ts">
  import { type Snippet } from "svelte";
  import CloseButton from "$lib/components/CloseButton.svelte";

  interface Props {
    open: boolean;
    title: string;
    children: Snippet;
  }

  let { open = $bindable(), title, children }: Props = $props();

  const position = $state({ x: 200, y: 150 });
  const size = $state({ width: 320, height: 200 });
  let isDragging = $state<boolean>(false);
  let isResizing = $state<boolean>(false);

  let startMouse = { x: 0, y: 0 };
  let startPos = { x: 0, y: 0 };
  let startSize = { width: 0, height: 0 };

  const clamp = (val: number, min: number, max: number) =>
    Math.max(min, Math.min(max, val));

  function startDrag(e: PointerEvent) {
    isDragging = true;
    startMouse = { x: e.clientX, y: e.clientY };
    startPos = { ...position };

    window.addEventListener("pointermove", onDrag);
    window.addEventListener("pointerup", stopDrag);
  }

  function onDrag(e: PointerEvent) {
    if (!isDragging) return;

    const deltaX = e.clientX - startMouse.x;
    const deltaY = e.clientY - startMouse.y;

    const maxX = window.innerWidth - size.width;
    const maxY = window.innerHeight - size.height;

    position.x = clamp(startPos.x + deltaX, 0, maxX);
    position.y = clamp(startPos.y + deltaY, 0, maxY);
  }

  function stopDrag() {
    isDragging = false;
    window.removeEventListener("pointermove", onDrag);
    window.removeEventListener("pointerup", stopDrag);
  }

  function startResize(e: PointerEvent) {
    e.stopPropagation();
    isResizing = true;

    startMouse = { x: e.clientX, y: e.clientY };
    startSize = { ...size };

    window.addEventListener("pointermove", onResize);
    window.addEventListener("pointerup", stopResize);
  }

  function onResize(e: PointerEvent) {
    if (!isResizing) return;

    size.width = Math.max(180, startSize.width + (e.clientX - startMouse.x));
    size.height = Math.max(120, startSize.height + (e.clientY - startMouse.y));
  }

  function stopResize() {
    isResizing = false;
    window.removeEventListener("pointermove", onResize);
    window.removeEventListener("pointerup", stopResize);
  }
</script>

<div
  class="window-container"
  style="
    left: {position.x}px;
    top: {position.y}px;
    width: {size.width}px;
    height: {size.height}px;
  "
>
  <header class="window-header" onpointerdown={startDrag}>
    <div class="header-title">{title}</div>
    <div class="header-buttons">
      <CloseButton onclick={() => (open = false)} />
    </div>
  </header>

  <main class="window-content">
    {@render children()}
  </main>

  <div class="resize-handle" onpointerdown={startResize}></div>
</div>

<style>
  .window-container {
    position: fixed;
    display: grid;
    grid-template-rows: auto 1fr;
    overflow: hidden;
    user-select: none;
    background: oklch(var(--color-primary));
  }

  .window-header {
    cursor: grab;
    display: grid;
    grid-template-columns: 1fr auto;
    padding: 0 var(--size-md);
    background: oklch(var(--color-accent));
    color: oklch(var(--color-text));
  }

  .header-buttons {
    display: flex;
  }

  .header-title {
    text-align: center;
  }

  .window-content {
    flex: 1;
    min-height: 0;
    overflow: hidden;
  }

  .resize-handle {
    position: absolute;
    right: 0;
    bottom: 0;
    width: var(--size-lg);
    height: var(--size-lg);
    cursor: se-resize;
    background: oklch(var(--color-text) / 0.5);
    clip-path: polygon(100% 100%, 100% 0, 0 100%);
  }
</style>
