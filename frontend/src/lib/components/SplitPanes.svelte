<script lang="ts">
  import { clamp } from "$lib/utils/math";
  import { untrack, type Snippet } from "svelte";

  interface Props {
    panes: Snippet[];
    direction?: "row" | "column";
  }

  const { panes, direction = "row" }: Props = $props();

  let paneSizes = $state<number[]>(
    untrack(() => panes).map(() => 100 / panes.length),
  );

  let dragIndex = $state<number | null>(null);
  let container: HTMLDivElement;

  function onMouseDown(index: number) {
    dragIndex = index;
  }

  function onMouseMove(e: MouseEvent) {
    if (dragIndex === null) return;

    const rect = container.getBoundingClientRect();
    const totalSize = direction === "row" ? rect.width : rect.height;
    const offset =
      direction === "row" ? e.clientX - rect.left : e.clientY - rect.top;

    const aheadSize = paneSizes
      .slice(0, dragIndex + 1)
      .reduce((a, b) => a + b, 0);

    const newHeadPercent = (offset / totalSize) * 100;
    const delta = newHeadPercent - aheadSize;

    const minSize = 10;
    const leftPane = paneSizes[dragIndex];
    const rightPane = paneSizes[dragIndex + 1];
    const clampedDelta = clamp(delta, -leftPane + minSize, rightPane - minSize);

    paneSizes = paneSizes.map((s, i) => {
      if (i === dragIndex) return s + clampedDelta;
      if (i === dragIndex + 1) return s - clampedDelta;
      return s;
    });
  }

  function onMouseUp() {
    dragIndex = null;
  }
</script>

<svelte:window onmousemove={onMouseMove} onmouseup={onMouseUp} />

<div
  class={["splitpanes", direction, { dragging: dragIndex !== null }]}
  bind:this={container}
>
  {#each panes as pane, i}
    <div
      class="pane"
      style={direction === "row"
        ? `width: ${paneSizes[i]}%`
        : `height: ${paneSizes[i]}%`}
    >
      {@render pane()}
    </div>

    {#if i < panes.length - 1}
      <div
        class={[
          "pane-splitter",
          `splitter-${direction}`,
          { active: dragIndex === i },
        ]}
        role="separator"
        aria-orientation={direction === "row" ? "vertical" : "horizontal"}
        onmousedown={() => onMouseDown(i)}
      ></div>
    {/if}
  {/each}
</div>

<style>
  .splitpanes {
    display: flex;
    width: 100%;
    height: 100%;
    overflow: hidden;

    &.row {
      flex-direction: row;
    }
    &.column {
      flex-direction: column;
    }
  }

  .pane {
    overflow: auto;
    flex-shrink: 0;
  }

  .pane-splitter {
    position: relative;
    flex-shrink: 0;
    z-index: 1;

    &.splitter-row {
      width: 0;
      cursor: col-resize;
    }

    &.splitter-column {
      height: 0;
      cursor: row-resize;
    }

    &::after {
      content: "";
      position: absolute;
      background: transparent;
      transition: background 0.15s;
    }

    &.splitter-row::after {
      top: 0;
      bottom: 0;
      left: -0.125rem;
      width: 0.25rem;
    }

    &.splitter-column::after {
      left: 0;
      right: 0;
      top: -0.125rem;
      height: 0.25rem;
    }

    &:hover::after,
    &.active::after {
      background: oklch(var(--color-accent));
    }
  }
</style>
