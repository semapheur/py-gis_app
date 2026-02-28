<script lang="ts">
  import { getAnnotateState } from "$lib/contexts/annotate.svelte";
  import { getImageViewerController } from "$lib/contexts/image_viewer/controller.svelte";
  import { getImageViewerState } from "$lib/contexts/image_viewer/state.svelte";
  import { getImageViewerOptions } from "$lib/contexts/context.svelte";

  const viewerOptions = getImageViewerOptions();

  const viewerController = getImageViewerController();
  const viewerState = getImageViewerState();

  $effect(() => {
    viewerController.updateInteractionMode(
      viewerState.activeSet,
      viewerState.activeMode,
    );
  });
</script>

{#if viewerOptions.imageInfo}
  <div
    class="map"
    {@attach (el) => {
      viewerController.attach(el, viewerOptions);
    }}
  ></div>
{/if}

<style>
  .map {
    width: 100%;
    height: 100%;
  }
</style>
