<script lang="ts">
  import { untrack } from "svelte";
  import { encode, decode } from "@msgpack/msgpack";
  import DaterangePicker from "$lib/components/DaterangePicker.svelte";
  import Input from "$lib/components/Input.svelte";
  import Button from "$lib/components/Button.svelte";
  import { toast } from "$lib/stores/toast.svelte";
  import { getImageViewerController } from "$lib/contexts/ol_image_viewer/controller.svelte";
  import { type DateRange } from "$lib/utils/date";
  import type { ImageMetadata } from "$lib/utils/types";

  interface Props {
    initialDateRange: DateRange;
    onFetch: (images: ImageMetadata[]) => void;
  }

  const { initialDateRange, onFetch }: Props = $props();

  let filename = $state<string | null>(null);
  let coverage = $state<number | null>(null);
  let iirs = $state<number | null>(null);
  let gsd = $state<number | null>(null);

  let dateRange = $state<DateRange>(untrack(() => initialDateRange));

  const viewer = getImageViewerController();

  async function submitForm(e: SubmitEvent) {
    e.preventDefault();

    const payload = {
      wkt: viewer.getViewExtentWkt(),
      filename,
      min_coverage: coverage,
      min_iirs: iirs,
      max_gsd: gsd,
      date_start: dateRange.start.getTime(),
      date_end: dateRange.end.getTime(),
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
    const { images, wkt } = decode(buffer) as {
      images: ImageMetadata[];
      wkt: string;
    };
    onFetch(images);
  }
</script>

<form class="form" onsubmit={submitForm}>
  <Button type="submit">Search</Button>
  <Input placeholder="File name" name="filename" bind:value={filename} />
  <Input
    placeholder="Min coverage (%)"
    name="min_coverage"
    bind:value={coverage}
    type="number"
    min="0"
    max="100"
  />
  <Input
    placeholder="Min IIRS"
    name="min_iirs"
    type="number"
    bind:value={iirs}
    min="0"
    max="9"
    step="any"
  />
  <Input
    placeholder="Max GSD (m)"
    name="max_gsd"
    type="number"
    bind:value={gsd}
    min="0"
    step="any"
  />
  <DaterangePicker bind:selectedRange={dateRange} />
</form>

<style>
  .form {
    display: flex;
    flex-wrap: wrap;
    gap: var(--size-md);
    width: 100%;
  }
</style>
