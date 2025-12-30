<script lang="ts">
  import { getAnnotateState } from "$lib/states/annotate.svelte";
  import { getImageViewerState } from "$lib/states/image_viewer.svelte";
  import type { ImageMetadata, RadiometricParams } from "$lib/utils/types";

  interface Props {
    image: ImageMetadata | null;
    radiometricParams: RadiometricParams | null;
  }

  let { image = null, radiometricParams = null }: Props = $props();
  const annotate = getAnnotateState();
  const viewer = getImageViewerState();

  $effect(() => {
    viewer.updateDrawInteraction(annotate);
  });
</script>

{#if image}
  <div
    class="map"
    {@attach (el) => {
      viewer.attach(el, { image, radiometricParams, annotate });
    }}
  ></div>
{/if}

<style>
  .map {
    width: 100%;
    height: 100%;
  }
</style>
