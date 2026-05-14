<script lang="ts">
  import type { PageData } from "./$types";
  import SplitPanes from "$lib/components/SplitPanes.svelte";
  import Map from "$lib/components/Map.svelte";
  import ImageSearchForm from "$lib/components/ImageSearchForm.svelte";
  import ImageGrid from "$lib/components/ImageGrid.svelte";
  import { setMapLibreState } from "$lib/contexts/ml_map.svelte";
  import type { ImageMetadata, ImagePreviewInfo } from "$lib/utils/types";
  import { WktParser } from "$lib/utils/geo/wkt";

  let { data }: { data: PageData } = $props();

  let imagePreview: ImagePreviewInfo | null = $state(null);

  const extentPolygon = $derived(
    data.wkt ? new WktParser(data.wkt).parsePolygon() : null,
  );

  setMapLibreState();

  function onHoverImage(image: ImageMetadata | null) {
    imagePreview = image
      ? {
          filename: image.filename,
          polygon: image.footprint,
          azimuth_angle: image.azimuth_angle,
          look_angle: image.look_angle,
        }
      : null;
  }
</script>

{#snippet leftPane()}
  <Map {imagePreview} {extentPolygon} />
{/snippet}

{#snippet rightPane()}
  <div class="right-pane">
    <ImageSearchForm />
    <ImageGrid images={data.images} {onHoverImage} />
  </div>
{/snippet}

<SplitPanes panes={[leftPane, rightPane]} />

<style>
  .right-pane {
    display: grid;
    grid-template-rows: auto 1fr;
    gap: var(--size-md);
    height: 100%;
    width: 100%;
    padding: var(--size-md);
  }
</style>
