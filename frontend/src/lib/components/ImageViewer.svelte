<script lang="ts">
  import { getImageViewerState } from "$lib/contexts/image_viewer/state.svelte";
  import { getImageViewerOptions } from "$lib/contexts/context.svelte";

  import ImageRenderer from "$lib/components/ImageRenderer.svelte";
  import AnnotateDialog from "$lib/components/AnnotateDialog.svelte";
  import AnnotationEdit from "$lib/components/AnnotationEdit.svelte";
  import AnnotationSummary from "$lib/components/AnnotationSummary.svelte";
  import MeasureDialog from "$lib/components/MeasureDialog.svelte";
  import ImageEnhacement from "$lib/components/ImageEnhacement.svelte";
  import Button from "$lib/components/Button.svelte";

  let annotateOpen = $state<boolean>(false);
  let summaryOpen = $state<boolean>(false);
  let enhancementOpen = $state<boolean>(false);
  let measurementOpen = $state<boolean>(false);

  const viewerState = getImageViewerState();
  viewerState.setActiveSet("annotation");
  viewerState.setActiveMode("edit");

  function openAnnotation() {
    annotateOpen = true;
    viewerState.setActiveSet("annotation");
  }

  function openMeasurement() {
    measurementOpen = true;
    viewerState.setActiveSet("measurement");
  }
</script>

<div class="container">
  {#if !annotateOpen}
    <div class="toggle-form">
      <Button onclick={() => openAnnotation()}>Add</Button>
    </div>
  {/if}
  {#if !summaryOpen}
    <div class="toggle-summary">
      <Button onclick={() => (summaryOpen = !summaryOpen)}>Summary</Button>
    </div>
  {/if}
  {#if !measurementOpen}
    <div class="toggle-measurement">
      <Button onclick={() => openMeasurement()}>Measure</Button>
    </div>
  {/if}
  <div class="toggle-enhancement">
    <Button onclick={() => (enhancementOpen = !enhancementOpen)}
      >Enhancement</Button
    >
  </div>
  {#if annotateOpen}
    <AnnotateDialog bind:open={annotateOpen} />
  {/if}
  <ImageRenderer />
  <AnnotationEdit />
  <AnnotationSummary bind:open={summaryOpen} />
  {#if enhancementOpen}
    <div class="enhancement">
      <ImageEnhacement />
    </div>
  {/if}
  {#if measurementOpen}
    <MeasureDialog bind:open={measurementOpen} />
  {/if}
</div>

<style>
  .container {
    position: relative;
    width: 100%;
    height: 100%;
  }

  .enhancement {
    position: absolute;
    top: var(--size-lg);
    right: var(--size-lg);
  }

  .toggle-form {
    position: absolute;
    left: var(--size-lg);
    bottom: var(--size-lg);
    z-index: 1;
  }

  .toggle-summary {
    position: absolute;
    right: var(--size-lg);
    bottom: var(--size-lg);
    z-index: 1;
  }

  .toggle-measurement {
    position: absolute;
    left: 50%;
    bottom: var(--size-lg);
    transform: translateX(-50%);
    z-index: 1;
  }

  .toggle-enhancement {
    position: absolute;
    top: var(--size-lg);
    right: var(--size-lg);
    z-index: 1;
  }
</style>
