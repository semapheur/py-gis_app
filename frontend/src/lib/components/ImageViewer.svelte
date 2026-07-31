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
  import GhostSearch from "$lib/components/GhostSearch.svelte";
  import CloseButton from "$lib/components/CloseButton.svelte";
  import Input from "$lib/components/Input.svelte";

  import { startOfDay, type DateRange } from "$lib/utils/date";
  import { toast } from "$lib/stores/toast.svelte";
  import type { ImageMetadata } from "$lib/utils/types";
  import ResizeableSidebar from "./ResizeableSidebar.svelte";
  import {
    parseCoordinates,
    toLatLon,
    type CoordinateType,
  } from "$lib/utils/geo/coord";
  import type { LatLon } from "$lib/utils/geo/latlon";

  const imageViewer = getImageViewerController();
  const viewerOptions = getImageViewerOptions();
  const viewerState = getImageViewerState();

  let leftSidebarOpen = $state<boolean>(false);
  let rightSidebarOpen = $state<boolean>(false);
  let annotateOpen = $state<boolean>(false);
  let summaryOpen = $state<boolean>(false);
  let enhancementOpen = $state<boolean>(false);
  let measurementOpen = $state<boolean>(false);
  let searchOpen = $state<boolean>(false);
  let ghostsOpen = $state<boolean>(false);
  let images = $state<ImageMetadata[]>([]);
  let coordinates = $state<string | null>(null);

  const initialDateRange = setInitialDateRange(3);

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
    const { images } = decode(buffer) as {
      images: ImageMetadata[];
      wkt: string;
    };
    return images;
  }

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

  function openGhost() {
    leftSidebarOpen = true;
    searchOpen = false;
    ghostsOpen = true;
    viewerState.setActiveSet("ghost");
  }

  function openSearch() {
    leftSidebarOpen = true;
    if (ghostsOpen) {
      imageViewer.clearGhosts();
      ghostsOpen = false;
    }
    searchOpen = true;
    searhImagesOnExtent().then((result) => {
      images = result;
    });
  }

  function closeLeftSidebar() {
    leftSidebarOpen = false;
    if (ghostsOpen) {
      imageViewer.clearGhosts();
      ghostsOpen = false;
      viewerState.setActiveSet(measurementOpen ? "measurement" : "annotation");
    }
  }

  function submitCoordinates() {
    if (!coordinates) return;
    let parsed;
    let latlon;
    try {
      parsed = parseCoordinates(coordinates) as CoordinateType;
      latlon = toLatLon(parsed) as LatLon;
    } catch {
      toast.error("Unsupported coordinate format");
      return;
    }
    console.log(latlon);
    const success = imageViewer.goToCoordinate(latlon.lonlat);
    if (!success) {
      toast.error("Coordinate is outside the image");
    }
  }

  $effect(() => {
    rightSidebarOpen = imageViewer.hasSelectedAnnotations;
  });
</script>

<div class="image-viewer">
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
    <Input
      class="coordinate-search-input"
      bind:value={coordinates}
      placeholder="Go to coordinates"
      onkeydown={(e) => e.key === "Enter" && submitCoordinates()}
    />
    <Button onclick={() => (enhancementOpen = !enhancementOpen)}
      >Enhancement</Button
    >
  </div>
  <div class="top-left">
    <Button onclick={() => openSearch()}>Extent search</Button>
    <Button onclick={() => openGhost()}>Ghosts</Button>
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
  <AnnotationSummary bind:open={summaryOpen} />
  {#if measurementOpen}
    <MeasureDialog bind:open={measurementOpen} />
  {/if}
  {#if leftSidebarOpen}
    <div class="left-sidebar">
      <div class="left-sidebar-button-group">
        <CloseButton onclick={closeLeftSidebar} />
      </div>
      {#if searchOpen}
        <ImageExtentSearch {initialDateRange} initialImages={images} />
      {:else if ghostsOpen}
        <GhostSearch />
      {/if}
    </div>
  {/if}
  {#if rightSidebarOpen}
    <ResizeableSidebar
      side="right"
      widthPercent={25}
      minWidthPercent={10}
      maxWidthPercent={50}
    >
      {#if imageViewer.hasSelectedAnnotations}
        <AnnotationEdit />
      {/if}
    </ResizeableSidebar>
  {/if}
</div>

<style>
  :global(.coordinate-search-input) {
    --input-font-size: 0.85rem;
  }

  .image-viewer {
    position: relative;
    width: 100%;
    height: 100%;
    background-color: oklch(var(--color-primary-accent));
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

  .left-sidebar-button-group {
    display: flex;
    justify-content: flex-end;
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
    display: flex;
    gap: var(--size-sm);
  }

  .top-left {
    position: absolute;
    top: var(--size-sm);
    left: var(--size-sm);
    z-index: 1;
  }
</style>
