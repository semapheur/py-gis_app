<script lang="ts">
  import { onMount } from "svelte";
  import { page } from "$app/state";
  import { Pane, Splitpanes } from "svelte-splitpanes";
  import Map from "$lib/components/Map.svelte";
  import ImageFilterForm from "$lib/components/ImageFilterForm.svelte";
  import ImageGrid from "$lib/components/ImageGrid.svelte";
  import { getPolygon } from "$lib/utils/searchStore";
  import type { ImageMetadata, ImagePreviewInfo } from "$lib/utils/types";

  const id = page.params.id;

  let polygon: GeoJSON.Polygon | null = $state(null);
  let images: ImageMetadata[] = $state([]);
  let loading = true;
  let error: string | null = null;
  let imagePreview: ImagePreviewInfo | null = $state(null);

  function onHoverImage(image: ImageMetadata | null) {
    imagePreview = image
      ? {
          filename: image.filename,
          coordinates: image.footprint.coordinates[0],
          azimuth_angle: image.azimuth_angle,
          look_angle: image.look_angle,
        }
      : null;
  }

  onMount(async () => {
    polygon = getPolygon(id);

    if (!polygon) {
      error = "Polygon not found or expired";
      loading = false;
      return;
    }

    try {
      const response = await fetch("/api/query-images", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(polygon),
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      images = await response.json();
      console.log(images);
    } catch (error) {
      console.error("Failed to fetch images:", error);
    } finally {
      loading = false;
    }
  });
</script>

<main class="container">
  <Splitpanes>
    <Pane>
      <Map extent={polygon} {imagePreview} />
    </Pane>
    <Pane>
      <ImageFilterForm />
      <ImageGrid {images} {onHoverImage} />
    </Pane>
  </Splitpanes>
</main>

<style>
  .container {
    width: 100%;
    height: 100%;
  }
</style>
