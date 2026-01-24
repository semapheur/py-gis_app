<script lang="ts">
  import { getAnnotateState } from "$lib/contexts/annotate.svelte";
  import { getImageViewerState } from "$lib/contexts/image_viewer.svelte";
  import type { ImageInfo, RadiometricParams } from "$lib/utils/types";

  interface Props {
    imageInfo: ImageInfo | null;
    radiometricParams: RadiometricParams | null;
  }

  let { imageInfo = null, radiometricParams = null }: Props = $props();
  const annotate = getAnnotateState();
  const viewer = getImageViewerState();

  $effect(() => {
    viewer.updateDrawInteraction(annotate);
  });
</script>

{#if imageInfo}
  <div
    class="map"
    {@attach (el) => {
      viewer.attach(el, { imageInfo, radiometricParams, annotate });
    }}
  ></div>
{/if}

<style>
  .map {
    width: 100%;
    height: 100%;
  }
</style>
