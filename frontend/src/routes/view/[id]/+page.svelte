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
  import ImageEnhacement from "$lib/components/ImageEnhacement.svelte";

  let { data } = $props<{ data: PageData }>();
  const imageInfo: ImageInfo = $derived(data.imageInfo);
  const radiometricParams: RadiometricParams = $derived(data.radiometricParams);
  const annotations = $derived(data.annotations);

  let annotateOpen = $state<boolean>(false);
  let summaryOpen = $state<boolean>(false);
  let enhancementOpen = $state<boolean>(false);

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
  <button
    class="toggle-enhancement"
    onclick={() => (enhancementOpen = !enhancementOpen)}>Enhancement</button
  >
  <AnnotateDialog bind:open={annotateOpen} />
  <ImageViewer {imageInfo} {radiometricParams} {annotations} />
  <AnnotationEdit />
  <AnnotationSummary bind:open={summaryOpen} />
  {#if enhancementOpen}
    <div class="enhancement">
      <ImageEnhacement />
    </div>
  {/if}
</div>

<style>
  .container {
    position: relative;
    width: 100%;
    height: 100%;
  }

  .enhancement {
    position: absolute;
    top: var(--size-lg);
    right: var(--size-lg);
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

  .toggle-enhancement {
    position: absolute;
    top: var(--size-lg);
    right: var(--size-lg);
    z-index: 1;
  }
</style>
