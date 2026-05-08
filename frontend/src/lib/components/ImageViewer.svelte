<script lang="ts">
  import { getImageViewerState } from "$lib/contexts/ol_image_viewer/state.svelte";

  import ImageRenderer from "$lib/components/ImageRenderer.svelte";
  import AnnotateDialog from "$lib/components/AnnotateDialog.svelte";
  import AnnotationEdit from "$lib/components/AnnotationEdit.svelte";
  import AnnotationSummary from "$lib/components/AnnotationSummary.svelte";
  import MeasureDialog from "$lib/components/MeasureDialog.svelte";
  import ImageEnhacement from "$lib/components/ImageEnhacement.svelte";
  import Button from "$lib/components/Button.svelte";
  import ImageFilterForm from "$lib/components/ImageFilterForm.svelte";
  import ImageGrid from "$lib/components/ImageGrid.svelte";
  import CloseButton from "$lib/components/CloseButton.svelte";

  let leftSidebarOpen = $state<boolean>(false);
  let annotateOpen = $state<boolean>(false);
  let summaryOpen = $state<boolean>(false);
  let enhancementOpen = $state<boolean>(false);
  let measurementOpen = $state<boolean>(false);
  let searchOpen = $state<boolean>(false);

  const viewerState = getImageViewerState();
  viewerState.setActiveSet("annotation");
  viewerState.setActiveMode("edit");

  function openAnnotation() {
    annotateOpen = true;
    measurementOpen = false;
    viewerState.setActiveSet("annotation");
  }

  function openMeasurement() {
    measurementOpen = true;
    annotateOpen = false;
    viewerState.setActiveSet("measurement");
  }
</script>

<div class="container">
  <div class="bottom-left">
    {#if !annotateOpen}
      <Button onclick={() => openAnnotation()}>Add</Button>
    {/if}
  </div>
  <div class="bottom-right">
    {#if !summaryOpen}
      <Button onclick={() => (summaryOpen = !summaryOpen)}>Summary</Button>
    {/if}
  </div>
  <div class="bottom-center">
    {#if !measurementOpen}
      <Button onclick={() => openMeasurement()}>Measure</Button>
    {/if}
  </div>
  <div class="top-right">
    <Button onclick={() => (enhancementOpen = !enhancementOpen)}
      >Enhancement</Button
    >
  </div>
  <div class="top-left">
    <Button
      onclick={() => {
        leftSidebarOpen = true;
        searchOpen = true;
      }}>Extent search</Button
    >
  </div>
  {#if enhancementOpen}
    <div class="enhancement">
      <ImageEnhacement />
    </div>
  {/if}
  {#if annotateOpen}
    <AnnotateDialog bind:open={annotateOpen} />
  {/if}
  <ImageRenderer />
  <AnnotationEdit />
  <AnnotationSummary bind:open={summaryOpen} />
  {#if measurementOpen}
    <MeasureDialog bind:open={measurementOpen} />
  {/if}
  {#if leftSidebarOpen}
    <div class="left-sidebar">
      <CloseButton onclick={() => (leftSidebarOpen = false)} />
      {#if searchOpen}
        <ImageFilterForm />
        <ImageGrid />
      {/if}
    </div>
  {/if}
</div>

<style>
  .container {
    position: relative;
    width: 100%;
    height: 100%;
  }

  .left-sidebar {
    position: absolute;
    top: 0;
    left: 0;
    width: 30%;
    height: 100%;
    padding: var(--size-md);
    background-color: oklch(var(--color-primary));
    z-index: 2;
  }

  .enhancement {
    position: absolute;
    top: var(--size-sm);
    right: var(--size-sm);
  }

  .bottom-left {
    position: absolute;
    left: var(--size-sm);
    bottom: var(--size-sm);
    z-index: 1;
  }

  .bottom-right {
    position: absolute;
    right: var(--size-sm);
    bottom: var(--size-sm);
    z-index: 1;
  }

  .bottom-center {
    position: absolute;
    left: 50%;
    bottom: var(--size-sm);
    transform: translateX(-50%);
    z-index: 1;
  }

  .top-right {
    position: absolute;
    top: var(--size-sm);
    right: var(--size-sm);
    z-index: 1;
  }

  .top-left {
    position: absolute;
    top: var(--size-sm);
    left: var(--size-sm);
    z-index: 1;
  }
</style>
