<script lang="ts">
  import type { PageData } from "./$types";
  import { Pane, Splitpanes } from "svelte-splitpanes";
  import Map from "$lib/components/Map.svelte";
  import ImageFilterForm from "$lib/components/ImageFilterForm.svelte";
  import ImageGrid from "$lib/components/ImageGrid.svelte";
  import { setMapLibreState } from "$lib/contexts/ml_map.svelte";
  import { wktToBbox } from "$lib/utils/geo/bbox";
  import type { ImageMetadata, ImagePreviewInfo } from "$lib/utils/types";
  import { WktParser } from "$lib/utils/geo/wkt";

  let { data }: { data: PageData } = $props();

  let imagePreview: ImagePreviewInfo | null = $state(null);

  const parsedPolygon = data.wkt
    ? new WktParser(data.wkt).parsePolygon()
    : null;
  const polygon = parsedPolygon ? [parsedPolygon] : [];
  const initialBbox = data.wkt ? wktToBbox(data.wkt) : null;

  setMapLibreState(polygon, initialBbox);

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

<Splitpanes>
  <Pane>
    <Map {imagePreview} />
  </Pane>
  <Pane>
    <div class="right-panel">
      <ImageFilterForm />
      <ImageGrid images={data.images} {onHoverImage} />
    </div>
  </Pane>
</Splitpanes>

<style>
  .right-panel {
    display: grid;
    grid-template-rows: auto 1fr;
    gap: var(--size-md);
    width: 100%;
    padding: var(--size-md);
  }
</style>
