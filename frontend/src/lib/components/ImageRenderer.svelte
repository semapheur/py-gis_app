<script lang="ts">
  import { getImageViewerController } from "$lib/contexts/ol_image_viewer/controller.svelte";
  import { getImageViewerState } from "$lib/contexts/ol_image_viewer/state.svelte";
  import { getImageViewerOptions } from "$lib/contexts/common.svelte";
  import ImageViewerContextMenu from "$lib/components/ImageViewerContextMenu.svelte";

  const viewerOptions = getImageViewerOptions();

  const viewerController = getImageViewerController();
  const viewerState = getImageViewerState();

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
    viewerController.attach(
      el,
      viewerOptions,
      viewerState.activeSet,
      viewerState.activeMode,
    );
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
</style>
