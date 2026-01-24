<script lang="ts">
  import {
    getAnnotateState,
    type AnnotationInfo,
  } from "$lib/contexts/annotate.svelte";
  import { getImageViewerState } from "$lib/contexts/image_viewer.svelte";
  import type { ImageInfo, RadiometricParams } from "$lib/utils/types";

  interface Props {
    imageInfo: ImageInfo | null;
    radiometricParams: RadiometricParams | null;
    annotations: AnnotationInfo[];
  }

  let {
    imageInfo = null,
    radiometricParams = null,
    annotations = [],
  }: Props = $props();
  const annotateState = getAnnotateState();
  const viewer = getImageViewerState();

  $effect(() => {
    viewer.updateDrawInteraction(annotateState);
  });
</script>

{#if imageInfo}
  <div
    class="map"
    {@attach (el) => {
      viewer.attach(el, {
        imageInfo,
        radiometricParams,
        annotateState,
        annotations,
      });
    }}
  ></div>
{/if}

<style>
  .map {
    width: 100%;
    height: 100%;
  }
</style>
