<script lang="ts">
  import type { PageData } from "./$types";
  import ImageViewer from "$lib/components/ImageViewer.svelte";

  export let data: PageData;

  const { image, radiometricParams } = data;
</script>

<ImageViewer {image} {radiometricParams} />
