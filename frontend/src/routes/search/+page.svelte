<script lang="ts">
  import type { PageData } from "./$types";
  import { Pane, Splitpanes } from "svelte-splitpanes";
  import Map from "$lib/components/Map.svelte";
  import ImageFilterForm from "$lib/components/ImageFilterForm.svelte";
  import ImageGrid from "$lib/components/ImageGrid.svelte";
  import { setMapLibreState } from "$lib/contexts/ml_map.svelte";
  import { wktToBbox, type BBox } from "$lib/utils/geo/bbox";
  import type { ImageMetadata, ImagePreviewInfo } from "$lib/utils/types";

  let { data }: { data: PageData } = $props();

  let bbox: BBox | null = $state(null);
  let imagePreview: ImagePreviewInfo | null = $state(null);

  setMapLibreState();

  $effect(() => {
    if (!data.wkt) {
      bbox = null;
      return;
    }

    bbox = wktToBbox(data.wkt);
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
    <Map extent={bbox} {imagePreview} />
  </Pane>
  <Pane>
    <ImageFilterForm />
    <ImageGrid images={data.images} {onHoverImage} />
  </Pane>
</Splitpanes>
