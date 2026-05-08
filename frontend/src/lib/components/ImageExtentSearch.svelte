<script lang="ts">
  import ImageGrid from "$lib/components/ImageGrid.svelte";
  import ImageSearchExtentForm from "$lib/components/ImageExtentSearchForm.svelte";
  import { type ImageMetadata } from "$lib/utils/types";

  let images = $state<ImageMetadata[]>([]);
</script>

<div class="image-extent-search">
  <ImageSearchExtentForm
    onFetch={(fetched: ImageMetadata[]) => (images = fetched)}
  />
  <ImageGrid {images} />
</div>
