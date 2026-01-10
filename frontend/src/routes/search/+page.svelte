<script lang="ts">
  import type { PageData } from "./$types";
  import { Pane, Splitpanes } from "svelte-splitpanes";
  import Map from "$lib/components/Map.svelte";
  import ImageFilterForm from "$lib/components/ImageFilterForm.svelte";
  import ImageGrid from "$lib/components/ImageGrid.svelte";
  import { WktParser } from "$lib/utils/geo/wkt";
  import type { ImageMetadata, ImagePreviewInfo } from "$lib/utils/types";
  import { setMapLibreState } from "$lib/contexts/maplibre.svelte";

  let { data }: { data: PageData } = $props();

  let polygon: GeoJSON.Polygon | null = $state(null);
  let imagePreview: ImagePreviewInfo | null = $state(null);

  setMapLibreState();

  $effect(() => {
    if (!data.wkt) {
      polygon = null;
      return;
    }

    polygon = new WktParser(data.wkt).parsePolygon();
  });

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

<Splitpanes>
  <Pane>
    <Map extent={polygon} {imagePreview} />
  </Pane>
  <Pane>
    <ImageFilterForm />
    <ImageGrid images={data.images} {onHoverImage} />
  </Pane>
</Splitpanes>
