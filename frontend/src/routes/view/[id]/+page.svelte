<script lang="ts">
  import type { PageData } from "./$types";
  import ImageViewer from "$lib/components/ImageViewer.svelte";
  import AnnotateDialog from "$lib/components/AnnotateDialog.svelte";
  import type {
    AnnotateForm,
    EquipmentData,
    ImageMetadata,
    RadiometricParams,
  } from "$lib/utils/types";

  let { data } = $props<{ data: PageData }>();
  const image: ImageMetadata = $derived(data.image);
  const radiometricParams: RadiometricParams = $derived(data.radiometricParams);

  let annotateOpen = $state(false);
  let drawMode = $state<boolean>(false);
  let drawLayer = $state<AnnotateForm>("equipment");
  let drawGeometry = $state<"Point" | "Polygon">("Point");
  let formData = $state<EquipmentData>();
</script>

<div class="container">
  {#if !annotateOpen}
    <button class="toggle-form" onclick={() => (annotateOpen = !annotateOpen)}>
      Add
    </button>
  {/if}
  <AnnotateDialog
    bind:open={annotateOpen}
    bind:drawMode
    bind:activeForm={drawLayer}
    bind:drawGeometry
    bind:formData
  />
  <ImageViewer
    {image}
    {radiometricParams}
    {formData}
    bind:drawMode
    bind:drawLayer
    bind:drawGeometry
  />
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
