<script lang="ts">
  import { untrack } from "svelte";
  import ImageGrid from "$lib/components/ImageGrid.svelte";
  import ImageSearchExtentForm from "$lib/components/ImageExtentSearchForm.svelte";
  import { type ImageMetadata } from "$lib/utils/types";
  import type { DateRange } from "$lib/utils/date";

  interface Props {
    initialImages: ImageMetadata[];
    initialDateRange: DateRange;
  }

  const { initialImages, initialDateRange }: Props = $props();
  let images = $state<ImageMetadata[]>(untrack(() => initialImages));
  $inspect(images);
</script>

<div class="image-extent-search">
  <ImageSearchExtentForm
    {initialDateRange}
    onFetch={(fetched: ImageMetadata[]) => (images = fetched)}
  />
  <ImageGrid {images} />
</div>

<style>
  .image-extent-search {
    display: flex;
    flex-direction: column;
    gap: var(--size-md);
    height: 100%;
  }
</style>
