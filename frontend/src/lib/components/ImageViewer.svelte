<script lang="ts">
  import { encode, decode } from "@msgpack/msgpack";
  import { getImageViewerState } from "$lib/contexts/ol_image_viewer/state.svelte";
  import { getImageViewerOptions } from "$lib/contexts/common.svelte";
  import { getImageViewerController } from "$lib/contexts/ol_image_viewer/controller.svelte";

  import ImageRenderer from "$lib/components/ImageRenderer.svelte";
  import AnnotateDialog from "$lib/components/AnnotateDialog.svelte";
  import AnnotationEdit from "$lib/components/AnnotationEdit.svelte";
  import AnnotationSummary from "$lib/components/AnnotationSummary.svelte";
  import MeasureDialog from "$lib/components/MeasureDialog.svelte";
  import ImageEnhacement from "$lib/components/ImageEnhacement.svelte";
  import Button from "$lib/components/Button.svelte";
  import ImageExtentSearch from "$lib/components/ImageExtentSearch.svelte";
  import CloseButton from "$lib/components/CloseButton.svelte";

  import { startOfDay, type DateRange } from "$lib/utils/date";
  import { toast } from "$lib/stores/toast.svelte";
  import type { ImageMetadata } from "$lib/utils/types";

  let leftSidebarOpen = $state<boolean>(false);
  let annotateOpen = $state<boolean>(false);
  let summaryOpen = $state<boolean>(false);
  let enhancementOpen = $state<boolean>(false);
  let measurementOpen = $state<boolean>(false);
  let searchOpen = $state<boolean>(false);
  let ghostsOpen = $state<boolean>(false);
  let images = $state<ImageMetadata[]>([]);

  const imageViewer = getImageViewerController();
  const viewerOptions = getImageViewerOptions();
  const viewerState = getImageViewerState();
  viewerState.setActiveSet("annotation");
  viewerState.setActiveMode("edit");

  const initialDateRange = setInitialDateRange(3);

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

  function setInitialDateRange(months: number) {
    const dateCollected = startOfDay(
      new Date(viewerOptions.imageInfo.datetime_collected),
    );
    const dateStart = new Date(dateCollected);
    dateStart.setMonth(dateCollected.getMonth() + months);
    const dateEnd = new Date(dateCollected);
    dateEnd.setMonth(dateCollected.getMonth() - months);

    const dateRange: DateRange = {
      start: dateStart,
      end: dateEnd,
    };
    return dateRange;
  }

  async function searhImagesOnExtent() {
    const payload = {
      wkt: imageViewer.getViewExtentWkt(),
      date_start: initialDateRange.start.getTime(),
      date_end: initialDateRange.start.getTime(),
    };

    const response = await fetch("/api/search-images", {
      method: "POST",
      headers: { "Content-Type": "application/msgpack" },
      body: encode(payload),
    });

    if (!response.ok) {
      toast.error("Failed to fetch images");
    }

    const buffer = await response.arrayBuffer();
    return decode(buffer) as ImageMetadata[];
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
        searhImagesOnExtent().then((result) => {
          images = result;
        });
      }}>Extent search</Button
    >
    <Button
      onclick={() => {
        leftSidebarOpen = true;
        ghostsOpen = true;
      }}>Ghosts</Button
    >
  </div>
  {#if enhancementOpen}
    <div class="enhancement">
      <ImageEnhacement bind:isOpen={enhancementOpen} />
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
        <ImageExtentSearch {initialDateRange} initialImages={images} />
      {:else if ghostsOpen}
        <GhostSearch />
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
    display: flex;
    flex-direction: column;
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
    z-index: 1;
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
