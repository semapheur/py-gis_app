<script lang="ts">
  import { getImageViewerController } from "#lib/contexts/ol_image_viewer/controller.svelte.js";
  import { getImageViewerState } from "#lib/contexts/ol_image_viewer/state.svelte.js";
  import { getImageViewerOptions } from "#lib/contexts/common.svelte.js";
  import ImageViewerContextMenu from "#lib/components/ImageViewerContextMenu.svelte";
  import { untrack } from "svelte";

  const viewerOptions = getImageViewerOptions();
  const viewerController = getImageViewerController();
  const viewerState = getImageViewerState();

  const imageKey = $derived(
    `${viewerOptions.imageInfo.id}:${viewerOptions.imageInfo.filename}`,
  );

  $effect(() => {
    viewerController.updateInteraction(
      viewerState.activeSet,
      viewerState.activeMode,
    );
  });
</script>

<div
  class="map"
  {@attach (el) => {
    imageKey;
    untrack(() =>
      viewerController.attach(
        el,
        viewerOptions,
        viewerState.activeSet,
        viewerState.activeMode,
      ),
    );
    return () => viewerController.detach();
  }}
>
  {#if viewerController.contextMenu}
    <ImageViewerContextMenu
      x={viewerController.contextMenu.x}
      y={viewerController.contextMenu.y}
      items={viewerController.contextMenu.items}
    />
  {/if}
</div>

<style>
  .map {
    width: 100%;
    height: 100%;
  }

  .map :global(canvas) {
    image-rendering: pixelated;
    image-rendering: crisp-edges;
  }

  .map :global(.ol-dragbox) {
    background-color: oklch(var(--color-secondary) / 0.1);
  }
</style>
