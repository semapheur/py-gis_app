<script lang="ts">
  import { setContext } from "svelte";
  import type { PageData } from "./$types";
  import ImageViewer from "$lib/components/ImageViewer.svelte";
  import AnnotateDialog from "$lib/components/AnnotateDialog.svelte";
  import AnnotationEdit from "$lib/components/AnnotationEdit.svelte";
  import AnnotationSummary from "$lib/components/AnnotationSummary.svelte";
  import type { ImageInfo, RadiometricParams } from "$lib/utils/types";
  import { setAnnotateState } from "$lib/contexts/annotate.svelte";
  import { setImageViewerState } from "$lib/contexts/image_viewer.svelte";

  let { data } = $props<{ data: PageData }>();
  const imageInfo: ImageInfo = $derived(data.imageInfo);
  const radiometricParams: RadiometricParams = $derived(data.radiometricParams);

  let annotateOpen = $state<boolean>(false);
  let summaryOpen = $state<boolean>(false);

  setContext("equipment-options", {
    confidenceOptions: data.confidenceOptions.options,
    statusOptions: data.statusOptions.options,
  });

  setAnnotateState();
  setImageViewerState();
</script>

<div class="container">
  {#if !annotateOpen}
    <button class="toggle-form" onclick={() => (annotateOpen = !annotateOpen)}>
      Add
    </button>
  {/if}
  {#if !summaryOpen}
    <button class="toggle-summary" onclick={() => (summaryOpen = !summaryOpen)}>
      Summary
    </button>
  {/if}
  <AnnotateDialog bind:open={annotateOpen} />
  <ImageViewer {imageInfo} {radiometricParams} />
  <AnnotationEdit />
  <AnnotationSummary bind:open={summaryOpen} />
</div>

<style>
  .container {
    position: relative;
    width: 100%;
    height: 100%;
  }

  .toggle-form {
    position: absolute;
    left: var(--size-lg);
    bottom: var(--size-lg);
    z-index: 1;
  }

  .toggle-summary {
    position: absolute;
    right: var(--size-lg);
    bottom: var(--size-lg);
    z-index: 1;
  }
</style>
