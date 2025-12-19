<script lang="ts">
  import type { PageData } from "./$types";
  import { Pane, Splitpanes } from "svelte-splitpanes";
  import Map from "$lib/components/Map.svelte";
  import ImageFilterForm from "$lib/components/ImageFilterForm.svelte";
  import ImageGrid from "$lib/components/ImageGrid.svelte";
  import type { ImageMetadata, ImagePreviewInfo } from "$lib/utils/types";

  let { data }: { data: PageData } = $props();

  let polygon: GeoJSON.Polygon | null = $state(null);
  let imagePreview: ImagePreviewInfo | null = $state(null);

  function onHoverImage(image: ImageMetadata | null) {
    imagePreview = image
      ? {
          filename: image.filename,
          coordinates: image.footprint!.coordinates[0],
          azimuth_angle: image.azimuth_angle,
          look_angle: image.look_angle,
        }
      : null;
  }
</script>

<main class="container">
  <Splitpanes>
    <Pane>
      <Map extent={polygon} {imagePreview} />
    </Pane>
    <Pane>
      <ImageFilterForm />
      <ImageGrid images={data.images} {onHoverImage} />
    </Pane>
  </Splitpanes>
</main>

<style>
  .container {
    width: 100%;
    height: 100%;
  }
</style>
