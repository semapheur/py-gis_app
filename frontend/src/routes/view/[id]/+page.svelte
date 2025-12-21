<script lang="ts">
  import type { PageData } from "./$types";
  import ImageViewer from "$lib/components/ImageViewer.svelte";
  import AnnotateDialog from "$lib/components/AnnotateDialog.svelte";

  let data: PageData = $props();
  let annotateOpen = $state(false);

  const { image, radiometricParams } = data;
</script>

<div class="container">
  <button class="toggle-form" onclick={() => (annotateOpen = !annotateOpen)}>
    Add
  </button>
  <AnnotateDialog bind:open={annotateOpen} />
  <ImageViewer {image} {radiometricParams} />
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
</style>
